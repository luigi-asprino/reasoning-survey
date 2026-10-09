# Code — loading-time tests, GraphDB

Default paths are relative to each script (inputs from `../data`, outputs to
`../results`), so the scripts can be run from any directory. Full usage in the
[GraphDB README](../README.md).

| Script | What it does | Reads | Writes | Needs |
|---|---|---|---|---|
| `benchmark_rulesets.py` | For each ruleset and run: creates a fresh `bench-ruleset-<ruleset>` repository, loads ontology and data (timed separately), records statement counts, deletes the repository. Prints a median summary. | `--ontology`, `--data` (default: `reasoning-capability-test/graphdb/data/university.ttl`) | `../results/benchmark_rulesets_<timestamp>.csv` | standard library |
| `ecmo-graphdb-benchmark.sh` | Wrapper around `benchmark_rulesets.py` for the ECMO ontology: selects modules, case fixtures, DUL/d0 or a DUL variant, sameAs mode and consistency checks. `--help` for the options. | `JRC/ecmo/0.3.1_audited`, `../data/dul-variants/`, `../data/ecmo-deps/` | `../results/ecmo_benchmark_*.csv` | bash, curl (to download DUL/d0) |
| `make_dul_variants.py` | Generates `DUL-lite.ttl` and `DUL-flat.ttl`. | DUL (file or download) | `../data/dul-variants/` | `rdflib` |

`benchmark_rulesets.py` also defines the `GraphDB` REST client (create/delete
repositories, load files, read sizes) used by
`reasoning-capability-test/graphdb/code/compare_implicit.py`; keep its
interface stable or update both.
