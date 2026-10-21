#!/usr/bin/env python3
"""
Loading-time benchmark of the Jena reasoners that Fuseki uses for inference
datasets (ja:InfModel), the counterpart of ../../graphdb/code/benchmark_rulesets.py.

Fuseki does not materialise inferences when data is loaded: a Jena reasoner
computes them in memory when the dataset is first used. So the cost of a
regime is measured as the time to compute the full closure, run in the Jena
engine directly (JenaLoadBench.java, with the Fuseki jar on the classpath):

  load ontology -> load data -> prepare() -> list all statements [-> validate()]

total_s = onto_load_s + data_load_s + prepare_s + closure_s is the analogue of
GraphDB's total_load_s (load + forward-chaining on commit). validate_s is
reported separately, as GraphDB's consistency checks are part of the commit.

One JVM per reasoner runs the warm-up and measured runs, so a timeout or an
out-of-memory error stops only that reasoner; it is recorded in the CSV.

Workloads:
  python benchmark_reasoners.py --jar FUSEKI_JAR                       # smoke test: university.ttl
  python benchmark_reasoners.py --jar FUSEKI_JAR --ecmo-workload --no-data            # setting 1
  python benchmark_reasoners.py --jar FUSEKI_JAR --ecmo-workload --no-data --consistency   # setting 2
  python benchmark_reasoners.py --jar FUSEKI_JAR --ecmo-workload --no-data --dul-lite      # setting 3
  python benchmark_reasoners.py --jar FUSEKI_JAR --ecmo-workload --no-data --dul-lite --consistency  # setting 4
  python benchmark_reasoners.py --jar FUSEKI_JAR --ecmo-workload --dul --reasoners none rdfs owl-mini

Writes ../results/benchmark_reasoners_<timestamp>.csv or
../results/ecmo_benchmark_<data|nodata>[_<dul variant>][_consistency]_<timestamp>.csv
and prints a median summary. Standard library only.
"""
import argparse
import csv
import json
import os
import statistics
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS_DIR = HERE.parent / "results"
GRAPHDB_DATA = HERE.parents[1] / "graphdb" / "data"           # dul-variants/, ecmo-deps/ (shared)
UNIVERSITY = HERE.parents[2] / "reasoning-capability-test" / "graphdb" / "data" / "university.ttl"
DEFAULT_ECMO = HERE.parents[3] / "ecmo" / "0.3.1_audited"        # JRC/ecmo, next to the reasoning repo
JAVA_SRC = HERE / "JenaLoadBench.java"

REASONERS = ["none", "transitive", "rdfs", "owl-micro", "owl-mini", "owl"]
CASE_FIXTURES = ["ecmo-ebola-case.ttl", "ecmo-hantavirus-case.ttl",
                 "ecmo-coreference-pattern-fixture.ttl", "ecmo-phsm-fixtures.ttl"]
DEPS = {"DUL.owl": "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl",
        "d0.owl": "http://www.ontologydesignpatterns.org/ont/d0.owl"}
FIELDS = ["reasoner", "run", "warmup", "onto_load_s", "data_load_s", "prepare_s", "closure_s",
          "total_s", "validate_s", "explicit", "inferred", "total", "inferred_ratio",
          "consistent", "error"]


def fetch_dep(name):
    path = GRAPHDB_DATA / "ecmo-deps" / name
    if not path.exists() or path.stat().st_size == 0:
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {DEPS[name]}")
        urllib.request.urlretrieve(DEPS[name], path)
    return path


def ecmo_files(args):
    ecmo = Path(args.ecmo).expanduser().resolve()
    if not ecmo.is_dir():
        sys.exit(f"ECMO folder not found: {ecmo}")
    onto, tag = [], []
    if args.dul_variant:
        dul = {"dul": None, "dul-lite": GRAPHDB_DATA / "dul-variants" / "DUL-lite.ttl",
               "dul-flat": GRAPHDB_DATA / "dul-variants" / "DUL-flat.ttl"}.get(args.dul_variant)
        dul = Path(args.dul_file) if args.dul_file else (dul or fetch_dep("DUL.owl"))
        onto += [dul, fetch_dep("d0.owl")]
    onto += sorted(ecmo.glob("ecmo-*.ttl")) + sorted((ecmo / "0.3.1-alignments").glob("*.ttl"))
    data = [] if args.no_data else [ecmo / "0.3.1-unittests" / f for f in CASE_FIXTURES
                                     if (ecmo / "0.3.1-unittests" / f).exists()]
    tag.append("nodata" if args.no_data else "data")
    if args.dul_variant:
        tag.append(f"dul-{Path(args.dul_file).stem}" if args.dul_file else args.dul_variant)
    if args.consistency:
        tag.append("consistency")
    return onto, data, "ecmo_benchmark_" + "_".join(tag)


def print_files(label, files):
    total = sum(f.stat().st_size for f in files)
    print(f"{label} files: {len(files)} ({total / 1024:,.0f} KB)")
    for i, f in enumerate(files, 1):
        print(f"  {i:>3}. {f}  ({f.stat().st_size / 1024:,.1f} KB)")


def run_reasoner(args, name, onto, data):
    cmd = ["java", f"-Xmx{args.xmx}", "-cp", str(Path(args.jar).expanduser()), str(JAVA_SRC),
           "--reasoner", name, "--runs", str(args.repetitions), "--warmup", str(args.warmup)]
    if args.consistency:
        cmd.append("--validate")
    cmd += ["--onto", *map(str, onto), "--data", *map(str, data)]
    print(f"{name:<12} {datetime.now():%H:%M:%S} started", flush=True)
    rows, err = [], None
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
        out, stderr = p.stdout, p.stderr
        if p.returncode not in (0, 3):
            err = f"JVM exited with code {p.returncode}: " + (stderr.strip().splitlines() or ["?"])[-1]
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = f"timeout after {args.timeout}s"
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("{"):
            rows.append(json.loads(line))
    if err:
        rows.append({"reasoner": name, "run": len(rows) + 1, "warmup": len(rows) < args.warmup, "error": err})
    for r in rows:
        if r.get("explicit") is not None and r.get("closure_s") is not None:
            r["total_s"] = round(sum(r.get(k) or 0 for k in ("onto_load_s", "data_load_s", "prepare_s", "closure_s")), 3)
            r["inferred_ratio"] = round(r["inferred"] / r["explicit"], 3) if r["explicit"] else 0
        for k in ("onto_load_s", "data_load_s", "prepare_s", "closure_s", "validate_s"):
            if isinstance(r.get(k), float):
                r[k] = round(r[k], 3)
        status = r.get("error") or ""
        if r.get("consistent") is False:
            status = "INCONSISTENT " + status
        if r.get("total_s") is not None:
            v = f"  validate {r['validate_s']:7.2f}s" if r.get("validate_s") is not None else ""
            print(f"{name:<12} run {r['run']}{' (warm-up)' if r['warmup'] else '':<10} "
                  f"load {r['onto_load_s'] + r['data_load_s']:7.2f}s  prepare {r['prepare_s']:7.2f}s  "
                  f"closure {r['closure_s']:7.2f}s  total {r['total_s']:7.2f}s{v}  "
                  f"explicit {r['explicit']:,}  inferred {r['inferred']:,}  {status}", flush=True)
        else:
            print(f"{name:<12} run {r['run']}  ERROR: {status}", flush=True)
    return rows


def summarize(rows, reasoners):
    ok = lambda r: not r.get("warmup") and r.get("total_s") is not None
    base_t = [r["total_s"] for r in rows if r["reasoner"] == "none" and ok(r)]
    base = statistics.median(base_t) if base_t else None
    print("\nSummary (median over non-warm-up runs)")
    hdr = f"{'reasoner':<12}{'runs':>5}{'total s':>10}{'stdev':>8}{'x none':>9}{'closure s':>11}{'validate s':>12}{'inferred':>14}{'inf/expl':>10}  consistent"
    print(hdr)
    print("-" * len(hdr))
    for name in reasoners:
        rr = [r for r in rows if r["reasoner"] == name and ok(r)]
        if not rr:
            errs = [r.get("error") for r in rows if r["reasoner"] == name and r.get("error")]
            print(f"{name:<12}{0:>5}   {errs[-1] if errs else 'no runs'}")
            continue
        t = [r["total_s"] for r in rr]
        med, sd = statistics.median(t), (statistics.stdev(t) if len(t) > 1 else 0.0)
        slow = f"{med / base:.1f}x" if base else "–"
        cl = statistics.median(r["closure_s"] for r in rr)
        vs = [r["validate_s"] for r in rr if r.get("validate_s") is not None]
        val = f"{statistics.median(vs):.2f}" if vs else "–"
        cons = {r.get("consistent") for r in rr} - {None}
        cons = "–" if not cons else ("yes" if cons == {True} else "NO")
        print(f"{name:<12}{len(rr):>5}{med:>10.2f}{sd:>8.2f}{slow:>9}{cl:>11.2f}{val:>12}"
              f"{rr[-1]['inferred']:>14,}{rr[-1]['inferred_ratio']:>10.2f}  {cons}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jar", default=os.environ.get("FUSEKI_JAR"),
                    help="fuseki-server.jar (bundles Jena); default: $FUSEKI_JAR")
    ap.add_argument("--reasoners", nargs="+", default=REASONERS, choices=REASONERS)
    ap.add_argument("--ontology", nargs="*", default=[], help="TBox files (ignored with --ecmo-workload)")
    ap.add_argument("--data", nargs="*", default=None, help="data files (default: university.ttl)")
    ap.add_argument("--ecmo-workload", action="store_true", help="ECMO modules + alignments as ontology, case fixtures as data")
    ap.add_argument("--ecmo", default=str(DEFAULT_ECMO), help="ECMO release folder")
    ap.add_argument("--no-data", action="store_true", help="with --ecmo-workload: ontology only")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dul", dest="dul_variant", action="store_const", const="dul", help="also load DUL + d0")
    g.add_argument("--dul-lite", dest="dul_variant", action="store_const", const="dul-lite")
    g.add_argument("--dul-flat", dest="dul_variant", action="store_const", const="dul-flat")
    ap.add_argument("--dul-file", help="with --dul: load this file instead of DUL")
    ap.add_argument("--consistency", action="store_true", help="also run validate() and record consistency")
    ap.add_argument("-n", "--repetitions", type=int, default=3)
    ap.add_argument("--warmup", type=int, default=1, help="warm-up runs per reasoner, excluded from the summary")
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per reasoner (all its runs)")
    ap.add_argument("--xmx", default="8g", help="JVM heap")
    ap.add_argument("-o", "--output", help="CSV output path")
    args = ap.parse_args()
    if not args.jar:
        sys.exit("Pass --jar <fuseki-dir>/fuseki-server.jar or set FUSEKI_JAR.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.ecmo_workload:
        onto, data, stem = ecmo_files(args)
    else:
        onto = [Path(f) for f in args.ontology]
        data = [Path(f) for f in (args.data if args.data is not None else [UNIVERSITY])]
        stem = "benchmark_reasoners"
    out = Path(args.output) if args.output else RESULTS_DIR / f"{stem}_{stamp}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Jena reasoners via {args.jar}  (heap {args.xmx}, timeout {args.timeout}s per reasoner, "
          f"{args.warmup} warm-up + {args.repetitions} runs, consistency={args.consistency})")
    print_files("Ontology", onto)
    print_files("Data", data)

    rows = []
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for name in args.reasoners:
            for r in run_reasoner(args, name, onto, data):
                rows.append(r)
                w.writerow(r)
                fh.flush()
    summarize(rows, args.reasoners)
    print(f"\nRaw results: {out.resolve()}")


if __name__ == "__main__":
    main()
