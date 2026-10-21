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
downloaded DUL/d0 are read from `../graphdb/data/`, ECMO from
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
