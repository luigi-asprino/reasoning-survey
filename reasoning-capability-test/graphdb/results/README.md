# Results — reasoning-capability tests, GraphDB

| File | Produced by | Content |
|---|---|---|
| `reasoning_report.md` | `../code/run_reasoning_tests.py` | Per query: the SPARQL, the rows returned by each repository, and what each repository misses relative to the union. Overwritten at every run. |
| `reasoning_report.json` | `../code/run_reasoning_tests.py` | Same results in machine-readable form. |
| `implicit_report.md` | `../code/compare_implicit.py` | Implicit triples of owl2-ql-optimized vs owl2-rl-optimized on `university.ttl`: per predicate, per class, and the triples only one ruleset infers. |
| `ecmo-inconsistencies.md` | written by hand, from `../code/check_disjointness.py` and the GraphDB consistency runs | Why ECMO 0.3.1 + DUL + the case fixtures is inconsistent (31 individuals, five groups of alignments) and a verified fix set. |

The findings drawn from these files are summarised in the
[GraphDB README](../README.md#findings-so-far) and in the notes
(`notes/dl-owl-expressivity.tex`).
