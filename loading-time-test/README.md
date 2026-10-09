# Loading-time tests

How much does each entailment regime cost? Triplestores that materialise
inferences at load time (forward chaining) pay for reasoning when data is
committed, so load time and store size measure the cost of a regime directly.

## Method

For every entailment regime, and for every repetition:

1. create a fresh repository configured with that regime;
2. load the ontology (TBox) files, timing them separately;
3. load the data (ABox) files, timing them;
4. record explicit, inferred and total statement counts;
5. delete the repository.

Warm-up runs are excluded from the summary, which reports the median load
time, its standard deviation, the slowdown compared with no reasoning, and the
ratio of inferred to explicit statements. Every run is kept in a CSV file.

Workloads:

- the test KG of the [reasoning-capability tests](../reasoning-capability-test/README.md)
  (`university.ttl`), as a smoke test: it loads in milliseconds;
- the ECMO ontology (all modules + alignments), optionally with the case
  fixtures as data and with DUL/d0, including lighter DUL variants without
  transitive/symmetric properties;
- optionally with consistency checks enabled, which also records whether the
  load was rejected as inconsistent.

## Triplestores

| Folder | Triplestore | Status |
|---|---|---|
| [`graphdb/`](graphdb/README.md) | Ontotext GraphDB 10.x | benchmark on all built-in rulesets except `rdfsplus*` |

Each triplestore folder contains `code/`, `data/` and `results/`; see the
[root README](../README.md#conventions) for the conventions.
