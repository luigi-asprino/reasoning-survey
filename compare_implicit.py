#!/usr/bin/env python3
"""
Explain why two GraphDB rulesets materialise different numbers of implicit
triples on the same data (e.g. owl2-ql vs owl2-rl).

For each of the two rulesets the script:
  1. creates a fresh repository configured with that ruleset
     (same configuration as benchmark_rulesets.py);
  2. loads the data files;
  3. fetches every implicit triple (FROM onto:implicit);
  4. deletes the repository (unless --keep).

It then reports, side by side:
  - implicit triples per predicate,
  - implicit rdf:type triples per class,
  - the triples only one ruleset infers, grouped by predicate, with examples.

Usage:
  python compare_implicit.py                                    # university.ttl, owl2-ql vs owl2-rl
  python compare_implicit.py --data university.ttl --rulesets owl2-ql-optimized owl2-rl-optimized
  python compare_implicit.py --data onto.ttl data.ttl --keep --report implicit_ecmo.md

Writes a Markdown report (default: implicit_report.md).
Standard library only; reuses the GraphDB client of benchmark_rulesets.py.
"""
import argparse
import json
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

from benchmark_rulesets import GraphDB

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
IMPLICIT_QUERY = """PREFIX onto: <http://www.ontotext.com/>
SELECT ?s ?p ?o FROM onto:implicit WHERE { ?s ?p ?o }"""

PREFIXES = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    "http://www.w3.org/2002/07/owl#": "owl:",
    "http://www.w3.org/2001/XMLSchema#": "xsd:",
    "http://example.org/": "ex:",
}


def short(term):
    for ns, p in PREFIXES.items():
        if term.startswith(ns):
            return p + term[len(ns):]
    return term


def fetch_implicit(db, repo):
    data = urllib.parse.urlencode({"query": IMPLICIT_QUERY, "infer": "true"}).encode()
    status, body = db.http("POST", f"/repositories/{repo}", data=data, timeout=None, headers={
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"})
    if status != 200:
        raise RuntimeError(f"[{repo}] query failed ({status}): {body[:300]}")

    def term(b):
        if b["type"] == "bnode":
            return "_:b"  # blank-node labels differ between repos; normalise
        if b["type"] == "literal":
            return f"\"{b['value']}\""
        return b["value"]

    return {(term(b["s"]), term(b["p"]), term(b["o"]))
            for b in json.loads(body)["results"]["bindings"]}


def materialise(db, ruleset, files, args):
    repo = f"{args.prefix}{ruleset}"
    if db.exists(repo):
        db.delete(repo)
    print(f"[{ruleset}] creating {repo}")
    db.create(repo, ruleset, args)
    try:
        for f in files:
            print(f"[{ruleset}] loading {f.name}")
            db.load_file(repo, f)
        explicit, inferred, _ = db.size(repo)
        triples = fetch_implicit(db, repo)
        print(f"[{ruleset}] explicit {explicit}, inferred {inferred}, fetched {len(triples)} implicit")
        return triples
    finally:
        if not args.keep:
            db.delete(repo)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def report(trip, a, b, args):
    md = [f"# Implicit triples: {a} vs {b}\n",
          f"Endpoint: `{args.url}` · data: {', '.join(args.data)} · "
          f"sameAs {'disabled' if args.disable_sameas else 'enabled'}\n"]
    md += table(["Ruleset", "Implicit triples"], [(r, len(trip[r])) for r in (a, b)]) + [""]

    pc = {r: Counter(p for _, p, _ in trip[r]) for r in (a, b)}
    preds = sorted(set(pc[a]) | set(pc[b]), key=lambda p: -(pc[a][p] + pc[b][p]))
    md += ["## Implicit triples per predicate\n"]
    md += table(["Predicate", a, b, f"{a} − {b}"],
                [(short(p), pc[a][p], pc[b][p], pc[a][p] - pc[b][p]) for p in preds]) + [""]

    tc = {r: Counter(o for _, p, o in trip[r] if p == RDF_TYPE) for r in (a, b)}
    classes = sorted(set(tc[a]) | set(tc[b]), key=lambda c: -(tc[a][c] + tc[b][c]))
    md += ["## Implicit rdf:type triples per class\n"]
    md += table(["Class", a, b, f"{a} − {b}"],
                [(short(c), tc[a][c], tc[b][c], tc[a][c] - tc[b][c]) for c in classes]) + [""]

    for x, y in ((a, b), (b, a)):
        only = trip[x] - trip[y]
        by_p = Counter(p for _, p, _ in only)
        md += [f"## Inferred only by {x} ({len(only)} triples)\n"]
        md += table(["Predicate", "Triples"], [(short(p), n) for p, n in by_p.most_common()]) + [""]
        for p, _ in by_p.most_common():
            ex = sorted(t for t in only if t[1] == p)[:args.examples]
            md += [f"**{short(p)}**, examples:\n", "```"]
            md += [f"{short(s)} {short(pp)} {short(o)}" for s, pp, o in ex] + ["```", ""]
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:7200", help="GraphDB base URL")
    ap.add_argument("--auth", help="user:password, if security is enabled")
    ap.add_argument("--data", nargs="+", default=["university.ttl"], help="files to load (ontology and data)")
    ap.add_argument("--rulesets", nargs=2, metavar=("A", "B"),
                    default=["owl2-ql-optimized", "owl2-rl-optimized"])
    ap.add_argument("--prefix", default="implicit-", help="prefix of the temporary repository ids")
    ap.add_argument("--disable-sameas", action=argparse.BooleanOptionalAction, default=False,
                    help="disable owl:sameAs handling (default: enabled, as in the reasoning-test-* repos)")
    ap.add_argument("--check-inconsistencies", action=argparse.BooleanOptionalAction, default=False)
    ap.add_argument("--entity-index-size", default="10000000")
    ap.add_argument("--keep", action="store_true", help="keep the two repositories after the run")
    ap.add_argument("--examples", type=int, default=5, help="example triples per predicate")
    ap.add_argument("--report", default="implicit_report.md")
    args = ap.parse_args()

    files = [Path(f) for f in args.data]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        sys.exit(f"File(s) not found: {', '.join(missing)}")

    db = GraphDB(args.url, args.auth)
    try:
        print(f"GraphDB {db.version()} at {args.url}")
    except Exception as e:
        sys.exit(f"Cannot reach GraphDB at {args.url}: {e}")

    a, b = args.rulesets
    trip = {r: materialise(db, r, files, args) for r in (a, b)}
    Path(args.report).write_text("\n".join(report(trip, a, b, args)) + "\n", encoding="utf-8")
    print(f"Report written to {args.report}")


if __name__ == "__main__":
    main()
