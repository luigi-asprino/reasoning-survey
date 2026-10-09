# Reasoning-capability tests

What does a SPARQL endpoint actually infer under each of its entailment
regimes? These tests load a small knowledge graph whose axioms are tagged with
the minimum regime expected to fire them, query it, and compare the answers
across regimes.

## Test design

- **Test KG** (`university.ttl`): ontology + data. Each axiom block is tagged
  with the minimum entailment regime expected to fire it, from RDFS to
  OWL 2 RL.
- **Query suite** (`queries.rq`): queries Q1–Q10, one construct family each
  (domain/range, inverse, symmetric, transitive, sameAs, intersection, union,
  property chains, keys, …), with the expected results in the comments.
- **Inconsistency tests** (`inconsistent.ttl`): three independent
  inconsistencies (disjointness, functional property + `owl:differentFrom`,
  disjointness via inferred range), to check whether consistency checking
  detects them.
- **Materialisation diff**: the implicit triples two regimes produce on the
  same data, grouped by predicate and class, to explain why the sizes differ.
- **Real ontology**: consistency of ECMO 0.3.1 + DUL + the case fixtures, with
  every disjointness violation explained.

The inputs are plain RDF and SPARQL, so they can be reused for any triplestore.

## Triplestores

| Folder | Triplestore | Status |
|---|---|---|
| [`graphdb/`](graphdb/README.md) | Ontotext GraphDB 10.x | rulesets compared; findings in the README |

Each triplestore folder contains `code/`, `data/` and `results/`; see the
[root README](../README.md#conventions) for the conventions.
