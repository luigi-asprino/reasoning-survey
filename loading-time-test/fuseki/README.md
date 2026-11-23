# Loading-time tests — Apache Jena Fuseki

Measures what each Jena reasoner (the engine behind Fuseki's inference
datasets) costs on the same workloads as the [GraphDB benchmark](../graphdb/README.md).

## What is measured, and how it differs from GraphDB

GraphDB materialises inferences when data is committed, so its load time
includes forward chaining. Fuseki does not: a dataset declared as
`ja:InfModel` keeps the data as loaded, and the Jena reasoner computes
inferences in memory the first time the dataset is used (forward rules in
`prepare()`, backward rules on demand at query time).

To get a comparable figure, the benchmark runs the Jena engine directly
(through the Fuseki jar, which bundles Jena) and forces the full closure:

| Step | Column | GraphDB analogue |
|---|---|---|
| parse the ontology files | `onto_load_s` | ontology load |
| parse the data files | `data_load_s` | data load |
| `InfModel.prepare()` | `prepare_s` | forward chaining on commit |
| list every statement of the InfModel | `closure_s` | (included in the commit) |
| sum of the four | `total_s` | `total_load_s` |
| `InfModel.validate()` (with `--consistency`) | `validate_s`, `consistent` | consistency checks on commit |

Notes:

- `closure_s` is an upper bound on what Fuseki pays at query time: a single
  query only triggers the backward rules it needs, whereas listing every
  statement triggers all of them.
- Jena has no switch for `owl:sameAs` handling, so there is no sameAs on/off mode.
- Unlike GraphDB, a Jena inference dataset is held in memory, so a large closure
  can fail with an out-of-memory error instead of filling the disk.

## Contents

| Path | Description |
|---|---|
| `code/benchmark_reasoners.py` | Benchmark driver: one JVM per reasoner (warm-up + measured runs), timeout per reasoner, CSV + median summary. Builds the ECMO workload like `ecmo-graphdb-benchmark.sh`. |
| `code/JenaLoadBench.java` | Runs one reasoner on the given files and prints one JSON line per run. Run by the driver; no build needed (Java 17+ source-file mode). |
| `results/` | One CSV per benchmark run. |

Inputs are shared with the GraphDB benchmark, not copied: DUL variants and the
downloaded DUL/d0 are read from the shared [`reasoning/data/`](../../data/README.md), ECMO from
`JRC/ecmo/0.3.1_audited`.

## Usage

Requires Java 17+ and the `fuseki-server.jar` of a Fuseki 5.x distribution
(pass it with `--jar` or set `FUSEKI_JAR`). Fuseki itself does not need to be
running. Python 3, standard library only. Commands written as run from this folder.

```bash
export FUSEKI_JAR=~/opt/apache-jena-fuseki-5.6.0/fuseki-server.jar

python code/benchmark_reasoners.py                                   # smoke test: university.ttl
python code/benchmark_reasoners.py --ecmo-workload --no-data                       # setting 1: ECMO alone
python code/benchmark_reasoners.py --ecmo-workload --no-data --consistency         # setting 2: + consistency
python code/benchmark_reasoners.py --ecmo-workload --no-data --dul-lite            # setting 3: + DUL-lite, d0
python code/benchmark_reasoners.py --ecmo-workload --no-data --dul-lite --consistency   # setting 4
python code/benchmark_reasoners.py --ecmo-workload --no-data --dul --reasoners none rdfs owl-micro   # full DUL
```

The reasoner `compiled` runs a rule profile generated from the ontology files by
[`jena-rule-profile/code/compile_rules.py`](../../jena-rule-profile/README.md)
(needs rdflib): forward rules only, so the inferences are materialised in
`prepare()`, and `--consistency` counts the violated checks it writes. It is
not in the default list:

```bash
python code/benchmark_reasoners.py --ecmo-workload --no-data --dul-lite --reasoners none rdfs compiled
python code/benchmark_reasoners.py --ecmo-workload --no-data --dul --reasoners compiled \
       --profile-args="--no-transitive dul:associatedWith --no-symmetric dul:associatedWith"
```

The profile is written next to the CSV (`.rules`); `--rules FILE` uses an
existing one and `--profile-args="..."` passes options to the compiler.

Options: `--reasoners` (default: `none transitive rdfs owl-micro owl-mini owl`),
`-n` measured runs (default 3), `--warmup` (default 1), `--timeout` seconds per
reasoner (default 1800), `--xmx` JVM heap (default `8g`), `--ecmo DIR`,
`--dul-flat`, `--dul-file FILE`, `-o` output path.

A reasoner that times out or runs out of memory is recorded with the error in
the CSV and the benchmark moves on to the next one.

## Results

CSV columns: `reasoner, run, warmup, onto_load_s, data_load_s, prepare_s,
closure_s, total_s, validate_s, explicit, inferred, total, inferred_ratio,
consistent, error`.

File names follow the GraphDB ones:

- `benchmark_reasoners_<timestamp>.csv` — generic benchmark;
- `ecmo_benchmark_<data|nodata>[_<dul variant>][_consistency]_<timestamp>.csv` — ECMO.

## Findings so far

ECMO 0.3.1, no data, compared with the GraphDB settings with owl:sameAs off
(single GraphDB run per ruleset; Jena: median of 3 runs after 1 warm-up, 8 GB heap,
30 min timeout per reasoner). Times in seconds.

| Workload | Jena reasoner | total s | inferred | GraphDB ruleset | total s | inferred |
|---|---|---|---|---|---|---|
| ECMO (setting 1) | transitive | 0.37 | 3,151 | – | | |
| | rdfs | 0.63 | 45,418 | rdfs-optimized | 1.9 | 38,918 |
| | owl-micro | 11.5 | 106,688 | owl-horst-optimized | 9.0 | 66,568 |
| | owl-mini, owl | not run | | owl-max / owl2-rl | 27.3 / 22.7 | 84,959 / 116,631 |
| ECMO + DUL-lite + d0 (setting 3) | transitive | 0.30 | 7,851 | – | | |
| | rdfs | 0.75 | 85,841 | rdfs-optimized | 6.6 | 79,169 |
| | owl-micro | out of memory | | owl-horst-optimized | 40.7 | 137,329 |
| | owl-mini, owl | timeout (> 30 min) | | owl-max / owl2-rl | 68.3 / 46.7 | 166,290 / 220,138 |

- Up to RDFS, Jena computes the closure faster than GraphDB materialises it,
  with a similar number of inferences (Jena's are slightly more because it also
  types every resource as `rdfs:Resource`).
- On ECMO alone, `owl-micro` is in the same range as GraphDB's OWL rulesets.
- Adding DUL-lite makes every Jena OWL reasoner fail: `owl-micro` runs out of
  memory while computing the closure (prepare() itself takes under a second),
  and `owl-mini` / `owl` don't finish in 30 minutes. GraphDB materialises the
  same workload with any ruleset in under 70 s and 220k inferences at most, so
  the entailments themselves fit easily in memory; the cost comes from how
  Jena's hybrid forward/backward engine evaluates them.
- The closure is a worst case: a query with a bound predicate triggers only
  part of the backward rules. Queries with an unbound predicate, or several
  queries together, approach it.

To do: setting 1 for `owl-mini` / `owl`; `owl-micro` with a larger heap
(`--xmx 24g`) to tell an out-of-memory error from a blow-up; DUL-flat, to check
whether DUL's remaining transitive and symmetric properties are the cause.
