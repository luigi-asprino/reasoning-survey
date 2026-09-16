#!/usr/bin/env python3
"""
Run the queries in queries.rq against several GraphDB repositories
(one per ruleset) and compare the results side by side.

Usage:
  python run_reasoning_tests.py                      # auto-discover reasoning-test-* repos
  python run_reasoning_tests.py --load               # clear + load university.ttl first
  python run_reasoning_tests.py --repos a b c        # explicit repo list
  python run_reasoning_tests.py --only Q1 Q5         # subset of queries
  python run_reasoning_tests.py --no-infer           # explicit data only (baseline)

Writes a Markdown report (default: reasoning_report.md) and a JSON dump.
Standard library only.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_REPO_PREFIX = "reasoning-test-"
SPARQL_JSON = "application/sparql-results+json"


# --------------------------------------------------------------------------- HTTP
def http(method, url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        sys.exit(f"Cannot reach GraphDB at {url}: {e.reason}")


def list_repos(base, prefix):
    status, body = http("GET", f"{base}/rest/repositories", headers={"Accept": "application/json"})
    if status != 200:
        sys.exit(f"Cannot list repositories ({status}): {body[:300]}")
    return sorted(r["id"] for r in json.loads(body) if r["id"].startswith(prefix))


def repo_ruleset(base, repo):
    status, body = http("GET", f"{base}/rest/repositories/{repo}", headers={"Accept": "application/json"})
    if status != 200:
        return "?"
    try:
        params = json.loads(body).get("params", {})
        rs = params.get("ruleset", {}).get("value", "?")
        same_as = params.get("disableSameAs", {}).get("value", "?")
        return f"{rs} (disableSameAs={same_as})"
    except (ValueError, AttributeError):
        return "?"


def load_data(base, repo, ttl_path, clear):
    stmts = f"{base}/repositories/{repo}/statements"
    if clear:
        status, body = http("DELETE", stmts)
        if status not in (200, 204):
            sys.exit(f"[{repo}] clear failed ({status}): {body[:300]}")
    status, body = http("POST", stmts, data=Path(ttl_path).read_bytes(),
                        headers={"Content-Type": "text/turtle"}, timeout=300)
    if status not in (200, 204):
        # consistency violations surface here (HTTP 500 with ConsistencyException)
        sys.exit(f"[{repo}] load failed ({status}): {body[:500]}")
    print(f"  loaded {ttl_path} into {repo}")


def run_query(base, repo, query, infer):
    url = f"{base}/repositories/{repo}"
    data = urllib.parse.urlencode({"query": query, "infer": str(infer).lower()}).encode()
    status, body = http("POST", url, data=data, headers={
        "Accept": SPARQL_JSON,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    if status != 200:
        return None, f"HTTP {status}: {body[:200].strip()}"
    return json.loads(body), None


# ------------------------------------------------------------------ query parsing
def parse_queries(path):
    """Split queries.rq into {id: (title, sparql)} sharing the PREFIX block."""
    text = Path(path).read_text(encoding="utf-8")
    prefixes = "\n".join(l for l in text.splitlines() if l.strip().upper().startswith("PREFIX"))
    body = "\n".join(l for l in text.splitlines() if not l.strip().upper().startswith("PREFIX"))
    queries = {}
    for chunk in re.split(r"(?m)^(?=#\s*Q\d+\b)", body):
        m = re.match(r"#\s*(Q\d+)\b(.*)", chunk)
        if not m:
            continue
        qid, title = m.group(1), m.group(2).strip()
        sparql = "\n".join(l for l in chunk.splitlines() if not l.lstrip().startswith("#")).strip()
        if sparql:
            queries[qid] = (title, f"{prefixes}\n{sparql}", sparql)
    return queries, prefixes


def prefix_map(prefix_block):
    return {iri: p for p, iri in re.findall(r"PREFIX\s+(\w*):\s*<([^>]+)>", prefix_block, re.I)}


def shorten(term, pmap):
    t, v = term["type"], term["value"]
    if t == "uri":
        for iri, p in sorted(pmap.items(), key=lambda kv: -len(kv[0])):
            if v.startswith(iri):
                return f"{p}:{v[len(iri):]}"
        return f"<{v}>"
    if t == "bnode":
        return "_:b"  # labels are arbitrary; normalise so repos compare equal
    return f'"{v}"'


def normalise(result, pmap):
    """Return (vars, sorted list of row-tuples)."""
    vars_ = result["head"]["vars"]
    rows = set()
    for b in result["results"]["bindings"]:
        rows.add(tuple(shorten(b[v], pmap) if v in b else "" for v in vars_))
    return vars_, sorted(rows)


# ------------------------------------------------------------------------ report
def fmt_rows(vars_, rows):
    if not rows:
        return "∅"
    if len(vars_) == 1:
        return ", ".join(r[0] for r in rows)
    return "; ".join("(" + ", ".join(f"{v}={x}" for v, x in zip(vars_, r) if x) + ")" for r in rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://localhost:7200")
    ap.add_argument("--repos", nargs="*", help=f"default: all repos starting with '{DEFAULT_REPO_PREFIX}'")
    ap.add_argument("--queries", default="queries.rq")
    ap.add_argument("--data", default="university.ttl")
    ap.add_argument("--load", action="store_true", help="clear each repo and load --data first")
    ap.add_argument("--no-clear", action="store_true", help="with --load, append instead of clearing")
    ap.add_argument("--only", nargs="*", help="query ids to run, e.g. Q1 Q5")
    ap.add_argument("--no-infer", action="store_true", help="query explicit statements only")
    ap.add_argument("--report", default="reasoning_report.md")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    repos = args.repos or list_repos(base, DEFAULT_REPO_PREFIX)
    if not repos:
        sys.exit("No repositories found.")

    print("Repositories:")
    rulesets = {r: repo_ruleset(base, r) for r in repos}
    for r in repos:
        print(f"  {r:35} {rulesets[r]}")

    if args.load:
        print("Loading data...")
        for r in repos:
            load_data(base, r, args.data, clear=not args.no_clear)

    queries, prefix_block = parse_queries(args.queries)
    if args.only:
        queries = {k: v for k, v in queries.items() if k in set(args.only)}
    pmap = prefix_map(prefix_block)
    pmap.setdefault("http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdf")
    pmap.setdefault("http://www.w3.org/2001/XMLSchema#", "xsd")

    infer = not args.no_infer
    md = [f"# GraphDB reasoning report\n", f"Endpoint: `{base}` · infer={infer}\n",
          "| Repository | Ruleset |", "|---|---|"]
    md += [f"| {r} | {rulesets[r]} |" for r in repos]
    dump = {}

    for qid, (title, sparql, body_only) in queries.items():
        print(f"\n=== {qid} {title}")
        md += [f"\n## {qid} — {title}\n", "```sparql", body_only, "```\n",
               "| Repository | #rows | Result |", "|---|---|---|"]
        results = {}
        for r in repos:
            res, err = run_query(base, r, sparql, infer)
            if err:
                results[r] = ("ERROR", err)
                print(f"  {r:35} ERROR {err}")
                md.append(f"| {r} | – | ERROR: {err} |")
                continue
            vars_, rows = normalise(res, pmap)
            results[r] = (vars_, rows)
            text = fmt_rows(vars_, rows)
            print(f"  {r:35} [{len(rows):>3}] {text}")
            cell = text.replace("|", "\\|")
            md.append(f"| {r} | {len(rows)} | {cell} |")

        # diff: what each repo adds/misses w.r.t. the union of all repos
        ok = {r: set(v[1]) for r, v in results.items() if v[0] != "ERROR"}
        if ok:
            union = set().union(*ok.values())
            md.append("")
            for r, rows in ok.items():
                missing = sorted(union - rows)
                if missing:
                    line = f"{r} missing: " + fmt_rows(results[r][0], missing)
                    print(f"  ↳ {line}")
                    md.append(f"- **{r}** missing: {fmt_rows(results[r][0], missing)}")
        dump[qid] = {r: (v if v[0] == "ERROR" else {"vars": v[0], "rows": v[1]})
                     for r, v in results.items()}

    Path(args.report).write_text("\n".join(md) + "\n", encoding="utf-8")
    Path(args.report).with_suffix(".json").write_text(json.dumps(dump, indent=2), encoding="utf-8")
    print(f"\nReport written to {args.report} (+ .json)")


if __name__ == "__main__":
    main()
