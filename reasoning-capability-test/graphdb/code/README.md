# Code — reasoning-capability tests, GraphDB

Python 3. Default paths are relative to each script (inputs from `../data`,
outputs to `../results`), so the scripts can be run from any directory.
Full usage in the [GraphDB README](../README.md).

| Script | What it does | Reads | Writes | Needs |
|---|---|---|---|---|
| `run_reasoning_tests.py` | Runs the query suite against the `reasoning-test-*` repositories and compares the answers side by side. | `../data/queries.rq`, `../data/university.ttl` (with `--load`) | `../results/reasoning_report.md` + `.json` | standard library |
| `compare_implicit.py` | Materialises the same data under two rulesets and reports the implicit triples each one infers. | `../data/university.ttl` | `../results/implicit_report.md` | standard library; imports `GraphDB` from `loading-time-test/graphdb/code/benchmark_rulesets.py` |
| `check_disjointness.py` | Lists every disjointness violation in ECMO + DUL + case data, with derivations (OWL 2 RL subset). | `JRC/ecmo/0.3.1_audited`, `loading-time-test/graphdb/data/` (DUL-lite, d0) | stdout | `rdflib` |

All GraphDB scripts expect GraphDB 10.x on `http://localhost:7200`
(`--base` / `--url` to change it).
