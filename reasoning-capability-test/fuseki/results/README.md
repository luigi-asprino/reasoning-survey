# Results — reasoning-capability tests, Fuseki

| File | Produced by | Content |
|---|---|---|
| `fuseki-config.ttl` | `../code/run_fuseki_tests.py` | Generated Fuseki configuration: one in-memory dataset per Jena reasoner. Rewritten at every run. |
| `fuseki_reasoning_report.md` | `../code/run_fuseki_tests.py` | Per query: the SPARQL, the rows returned by each dataset, query time, and what each dataset misses relative to the union. Overwritten at every run. |
| `fuseki_reasoning_report.json` | `../code/run_fuseki_tests.py` | Same results in machine-readable form. |
| `fuseki.log` | Fuseki, when started by `run_fuseki_tests.py --fuseki` | Server log of the last run. |
| `jena_reasoners_report.md` | `../code/JenaReasoners.java` | Preparation time, implicit triples per predicate, validation reports (not yet produced). |
| `jena_consistency_report.md` | `../code/JenaReasoners.java --validate-only` | Consistency of `inconsistent.ttl` under each reasoner (not yet produced). |

The findings are summarised in the [Fuseki README](../README.md#findings-so-far)
and, side by side with GraphDB, in [`../../SUMMARY.md`](../../SUMMARY.md).
