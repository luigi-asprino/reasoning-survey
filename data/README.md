# Shared data — DUL versions and ECMO dependencies

Ontology inputs shared by every test and triplestore (GraphDB and Fuseki
loading-time benchmarks, `check_disjointness.py`, the Jena rule profile).
The test KG and query suite of the reasoning-capability tests stay in
`reasoning-capability-test/graphdb/data/`.

The ECMO ontology itself is not here: it is read from the `ecmo` repository
next to this one (`JRC/ecmo/0.3.1_audited`).

| Path | Content | Tracked |
|---|---|---|
| `dul-variants/` | Other versions of DUL: the lighter variants without transitive/symmetric properties and DUL 4.3; see its [README](dul-variants/README.md). | yes |
| `ecmo-deps/` | `DUL.owl` and `d0.owl`, downloaded by `ecmo-graphdb-benchmark.sh --dul` or `benchmark_reasoners.py --dul` on first use (`DUL.owl` is Turtle despite the extension). | no (git-ignored) |
