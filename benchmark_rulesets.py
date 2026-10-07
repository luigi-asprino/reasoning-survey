#!/usr/bin/env python3
"""
Measure the impact of GraphDB rulesets (entailment regimes) on loading time.

For every ruleset and every repetition the script:
  1. creates a fresh repository configured with that ruleset (GraphDB 10.x config);
  2. loads the ontology (TBox) files, if any, timing them separately;
  3. loads the data (ABox) files, timing them;
  4. reads explicit / inferred / total statement counts;
  5. deletes the repository (the last one per ruleset survives with --keep).

GraphDB materialises inferences at load time (forward chaining) and the RDF4J
statements endpoint answers only after the commit, so wall-clock load time
includes the full cost of each entailment regime.

Results go to a CSV file (one row per run); a median summary is printed.
Temporary repositories are named bench-ruleset-<ruleset>, so the
reasoning-test-* repositories are never touched.

Usage:
  python benchmark_rulesets.py                                  # university.ttl, all rulesets
  python benchmark_rulesets.py --ontology onto.ttl --data data1.ttl data2.nt.gz -n 5
  python benchmark_rulesets.py --data big.nt.gz \\
      --rulesets empty rdfs-optimized owl-horst-optimized owl2-rl-optimized --keep
  python benchmark_rulesets.py --disable-sameas                 # GraphDB's own default

Standard library only.
"""
import argparse
import base64
import csv
import gzip
import json
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

# rdfsplus / rdfsplus-optimized are deliberately excluded: they do not apply
# rdfs:domain / rdfs:range (see README, "Findings so far").
DEFAULT_RULESETS = [
    "empty",
    "rdfs", 
    "owl-horst", 
    "owl-max", 
    "owl2-ql", 
    "owl2-rl", 
    "rdfs-optimized",
    "owl2-ql-optimized",
    "owl-horst-optimized",
    "owl-max-optimized",
    "owl2-rl-optimized"
]

CONTENT_TYPES = {
    ".ttl": "text/turtle",
    ".nt": "application/n-triples",
    ".nq": "application/n-quads",
    ".trig": "application/trig",
    ".rdf": "application/rdf+xml",
    ".owl": "application/rdf+xml",
    ".xml": "application/rdf+xml",
    ".jsonld": "application/ld+json",
    ".n3": "text/n3",
}

# parser to retry with when the one chosen from the extension fails
# (.owl files are often Turtle, e.g. DUL.owl)
FALLBACK_FORMATS = {"application/rdf+xml": "text/turtle"}

REPO_CONFIG_TEMPLATE = """\
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep:     <http://www.openrdf.org/config/repository#> .
@prefix sr:      <http://www.openrdf.org/config/repository/sail#> .
@prefix sail:    <http://www.openrdf.org/config/sail#> .
@prefix graphdb: <http://www.ontotext.com/config/graphdb#> .

[] a rep:Repository ;
   rep:repositoryID "{repo_id}" ;
   rdfs:label "Ruleset benchmark: {ruleset}" ;
   rep:repositoryImpl [
      rep:repositoryType "graphdb:SailRepository" ;
      sr:sailImpl [
         sail:sailType "graphdb:Sail" ;
         graphdb:ruleset "{ruleset}" ;
         graphdb:disable-sameAs "{disable_sameas}" ;
         graphdb:check-for-inconsistencies "{check_inconsistencies}" ;
         graphdb:entity-index-size "{entity_index_size}" ;
         graphdb:entity-id-size "32" ;
         graphdb:enable-context-index "false" ;
         graphdb:enablePredicateList "true" ;
         graphdb:in-memory-literal-properties "true" ;
         graphdb:enable-literal-index "true" ;
         graphdb:query-timeout "0" ;
         graphdb:throw-QueryEvaluationException-on-timeout "false" ;
         graphdb:read-only "false"
      ]
   ] .
"""


# --------------------------------------------------------------------------- HTTP
class GraphDB:
    def __init__(self, base, auth=None):
        self.base = base.rstrip("/")
        self.headers = {}
        self.format_cache = {}  # path -> content type that parsed successfully
        if auth:
            self.headers["Authorization"] = "Basic " + base64.b64encode(auth.encode()).decode()

    def http(self, method, path, data=None, headers=None, timeout=60):
        h = dict(self.headers, **(headers or {}))
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")

    def version(self):
        status, body = self.http("GET", "/rest/info/version", headers={"Accept": "application/json"})
        if status != 200:
            raise RuntimeError(f"HTTP {status}: {body[:200]}")
        return json.loads(body).get("productVersion", "?")

    def exists(self, repo):
        status, body = self.http("GET", "/rest/repositories", headers={"Accept": "application/json"})
        if status != 200:
            raise RuntimeError(f"Cannot list repositories ({status}): {body[:300]}")
        return any(r.get("id") == repo for r in json.loads(body))

    def create(self, repo, ruleset, args):
        cfg = REPO_CONFIG_TEMPLATE.format(
            repo_id=repo,
            ruleset=ruleset,
            disable_sameas=str(args.disable_sameas).lower(),
            check_inconsistencies=str(args.check_inconsistencies).lower(),
            entity_index_size=args.entity_index_size,
        ).encode()
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="config"; filename="config.ttl"\r\n'
                f"Content-Type: text/turtle\r\n\r\n").encode() + cfg + f"\r\n--{boundary}--\r\n".encode()
        status, resp = self.http("POST", "/rest/repositories", data=body, timeout=120,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        if status >= 300:
            raise RuntimeError(f"Cannot create {repo} ({status}): {resp[:300]}")
        for _ in range(120):  # wait until the repository answers
            if self.http("GET", f"/repositories/{repo}/size")[0] == 200:
                return
            time.sleep(0.5)
        raise RuntimeError(f"Repository {repo} did not become ready")

    def delete(self, repo):
        self.http("DELETE", f"/rest/repositories/{repo}", timeout=300)

    def _post_file(self, repo, path, gz, ctype):
        headers = {"Content-Type": ctype}
        if not gz:
            headers["Content-Length"] = str(path.stat().st_size)
        # .gz files are decompressed on the fly and streamed with chunked transfer encoding
        with (gzip.open if gz else open)(path, "rb") as fh:
            return self.http("POST", f"/repositories/{repo}/statements",
                             data=fh, headers=headers, timeout=None)

    def load_file(self, repo, path):
        """Load one file. Returns the seconds spent on failed parse attempts, so
        callers can exclude them from the timing."""
        suffixes = [s.lower() for s in path.suffixes]
        gz = bool(suffixes) and suffixes[-1] == ".gz"
        ext = suffixes[-2] if gz and len(suffixes) > 1 else (suffixes[-1] if suffixes else "")
        ctype = self.format_cache.get(path) or CONTENT_TYPES.get(ext)
        if ctype is None:
            raise ValueError(f"Unknown RDF format for {path} (extension '{ext}')")
        t0 = time.perf_counter()
        status, body = self._post_file(repo, path, gz, ctype)
        wasted = 0.0
        fallback = FALLBACK_FORMATS.get(ctype)
        if 400 <= status < 500 and fallback and path not in self.format_cache:
            # parse error (e.g. a .owl file that is actually Turtle): the failed
            # transaction is rolled back, so retry with the fallback parser
            wasted = time.perf_counter() - t0
            status2, body2 = self._post_file(repo, path, gz, fallback)
            if status2 < 300:
                print(f"  note: {path.name} is not {ctype}; loaded as {fallback}")
                self.format_cache[path] = fallback
                return wasted
            body = f"{body[:250]} | retry as {fallback} ({status2}): {body2[:250]}"
        if status >= 300:
            # consistency violations surface here (HTTP 500 with ConsistencyException)
            raise RuntimeError(f"Load of {path} failed ({status}): {body[:500]}")
        self.format_cache[path] = ctype
        return wasted

    def size(self, repo):
        """Returns (explicit, inferred, total)."""
        status, body = self.http("GET", f"/rest/repositories/{repo}/size", timeout=300,
                                 headers={"Accept": "application/json"})
        if status == 200:
            j = json.loads(body)
            return j["explicit"], j["inferred"], j["total"]
        # fallback: RDF4J size (explicit) + SPARQL count with inference
        explicit = int(self.http("GET", f"/repositories/{repo}/size", timeout=300)[1])
        q = urllib.parse.urlencode({"query": "SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }",
                                    "infer": "true"})
        status, body = self.http("GET", f"/repositories/{repo}?{q}", timeout=None,
                                 headers={"Accept": "application/sparql-results+json"})
        total = int(json.loads(body)["results"]["bindings"][0]["c"]["value"])
        return explicit, total - explicit, total


# --------------------------------------------------------------------------- benchmark
def timed_load(db, repo, files, tag, what):
    if not files:
        return 0.0
    print(f"{tag:<34} {datetime.now():%H:%M:%S} loading {len(files)} {what} file(s)...", flush=True)
    t0 = time.perf_counter()
    wasted = sum(db.load_file(repo, f) for f in files)
    return time.perf_counter() - t0 - wasted


def run(args):
    db = GraphDB(args.url, args.auth)
    try:
        print(f"GraphDB {db.version()} at {args.url}  (disable-sameAs={args.disable_sameas}, "
              f"check-for-inconsistencies={args.check_inconsistencies})")
    except (urllib.error.URLError, RuntimeError, ValueError) as e:
        sys.exit(f"Cannot reach GraphDB at {args.url}: {e}")

    onto = [Path(p) for p in args.ontology]
    data = [Path(p) for p in args.data]
    for p in onto + data:
        if not p.exists():
            sys.exit(f"File not found: {p}")

    out = Path(args.output or f"benchmark_rulesets_{datetime.now():%Y%m%d_%H%M%S}.csv")
    fields = ["ruleset", "run", "warmup", "onto_load_s", "data_load_s", "total_load_s",
              "explicit", "inferred", "total", "inferred_ratio", "error"]
    rows = []
    runs = args.warmup + args.repetitions

    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for ruleset in args.rulesets:
            repo = f"{args.prefix}{ruleset}"
            for i in range(runs):
                warm = i < args.warmup
                row = {"ruleset": ruleset, "run": i + 1, "warmup": warm}
                tag = f"[{ruleset} #{i + 1}{' warmup' if warm else ''}]"
                try:
                    if db.exists(repo):
                        db.delete(repo)
                    db.create(repo, ruleset, args)
                    t_onto = timed_load(db, repo, onto, tag, "ontology")
                    t_data = timed_load(db, repo, data, tag, "data")
                    ex, inf, tot = db.size(repo)
                    row.update(onto_load_s=round(t_onto, 3), data_load_s=round(t_data, 3),
                               total_load_s=round(t_onto + t_data, 3),
                               explicit=ex, inferred=inf, total=tot,
                               inferred_ratio=round(inf / ex, 3) if ex else None)
                    print(f"{tag:<34} onto {t_onto:8.2f}s  data {t_data:8.2f}s  "
                          f"explicit {ex:>12,}  inferred {inf:>12,}")
                except Exception as e:  # keep going with the other rulesets
                    row["error"] = str(e)[:300]
                    print(f"{tag:<34} ERROR: {e}")
                finally:
                    if not (args.keep and i == runs - 1):
                        try:
                            db.delete(repo)
                        except Exception:
                            pass
                w.writerow(row)
                fh.flush()
                rows.append(row)

    summarize(rows, args.rulesets)
    print(f"\nRaw results: {out.resolve()}")


def summarize(rows, rulesets):
    ok = [r for r in rows if not r["warmup"] and not r.get("error")]
    base_times = [r["total_load_s"] for r in ok if r["ruleset"] == "empty"]
    base = statistics.median(base_times) if base_times else None
    print("\nSummary (median over non-warm-up runs)")
    hdr = f"{'ruleset':<22}{'runs':>5}{'load s':>10}{'stdev':>8}{'x empty':>9}{'inferred':>14}{'inf/expl':>10}"
    print(hdr)
    print("-" * len(hdr))
    for rs in rulesets:
        rr = [r for r in ok if r["ruleset"] == rs]
        if not rr:
            print(f"{rs:<22}{0:>5}   (no successful runs)")
            continue
        t = [r["total_load_s"] for r in rr]
        med = statistics.median(t)
        sd = statistics.stdev(t) if len(t) > 1 else 0.0
        slow = f"{med / base:.2f}" if base else "-"
        ratio = rr[-1]["inferred_ratio"]
        print(f"{rs:<22}{len(rr):>5}{med:>10.2f}{sd:>8.2f}{slow:>9}"
              f"{rr[-1]['inferred']:>14,}{ratio if ratio is not None else '-':>10}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:7200", help="GraphDB base URL")
    ap.add_argument("--auth", help="user:password, if security is enabled")
    ap.add_argument("--ontology", nargs="*", default=[], help="TBox files, loaded (and timed) first")
    ap.add_argument("--data", nargs="*", default=["university.ttl"],
                    help="data files (.ttl .nt .nq .trig .rdf .owl .jsonld .n3, optionally .gz); "
                         "pass --data with no files to load the ontology only")
    ap.add_argument("--rulesets", nargs="+", default=DEFAULT_RULESETS)
    ap.add_argument("-n", "--repetitions", type=int, default=3)
    ap.add_argument("--warmup", type=int, default=1, help="warm-up runs per ruleset, excluded from the summary")
    ap.add_argument("--prefix", default="bench-ruleset-", help="prefix of the temporary repository ids")
    ap.add_argument("--disable-sameas", action=argparse.BooleanOptionalAction, default=False,
                    help="disable owl:sameAs handling (default: enabled, as in the reasoning-test-* repos)")
    ap.add_argument("--check-inconsistencies", action=argparse.BooleanOptionalAction, default=False)
    ap.add_argument("--entity-index-size", default="10000000")
    ap.add_argument("--keep", action="store_true", help="keep the last repository of each ruleset")
    ap.add_argument("-o", "--output", help="CSV output path")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
