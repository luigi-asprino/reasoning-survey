# Data — loading-time tests, GraphDB

The ECMO ontology itself is not here: it is read from the `ecmo` repository
next to this one (`JRC/ecmo/0.3.1_audited`).

| Path | Content | Tracked |
|---|---|---|
| `dul-variants/` | Lighter versions of DUL without transitive/symmetric properties; see its [README](dul-variants/README.md). Also used by `reasoning-capability-test/graphdb/code/check_disjointness.py`. | yes |
| `ecmo-deps/` | `DUL.owl` and `d0.owl`, downloaded by `ecmo-graphdb-benchmark.sh --dul` on first use (`DUL.owl` is Turtle despite the extension). | no (git-ignored) |
