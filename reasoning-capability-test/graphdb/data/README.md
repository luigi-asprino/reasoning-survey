# Data — reasoning-capability tests, GraphDB

Test inputs. They are plain RDF and SPARQL, so they can be reused for other
triplestores.

| File | Content |
|---|---|
| `university.ttl` | Test ontology + data (namespace `http://example.org/`). Each axiom block is tagged with the minimum ruleset expected to fire it, from RDFS to OWL 2 RL. Also the default data of `loading-time-test/graphdb/code/benchmark_rulesets.py`. |
| `queries.rq` | Queries Q1–Q10, one construct family each, sharing one PREFIX block. Each query starts with a `# Qn title` comment and lists its expected results in the comments; `run_reasoning_tests.py` splits the file on those headers. |
| `inconsistent.ttl` | Three independent inconsistencies: disjointness, functional property + `owl:differentFrom`, disjointness via inferred range. Load one at a time into a repository with consistency checks enabled. |

When adding a query, keep the `# Qn title` header format and write the
expected result in the comments, so the report can be checked by eye.
