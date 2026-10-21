# Reasoning-capability tests — summary of results

Same test KG ([`university.ttl`](graphdb/data/university.ttl)) and query suite
([`queries.rq`](graphdb/data/queries.rq), Q1–Q9) run on two triplestores:

- **GraphDB**: one repository per ruleset, with the inferences materialised at load time.
- **Apache Jena Fuseki 5**: one in-memory dataset per Jena reasoner, with the reasoning done when the dataset is first queried.

Detailed per-query outputs:

- GraphDB: [`graphdb/results/reasoning_report.md`](graphdb/results/reasoning_report.md)
- Fuseki: [`fuseki/results/fuseki_reasoning_report.md`](fuseki/results/fuseki_reasoning_report.md)

## Which constructs each regime handles

✓ = the expected answers are returned; ◐ = only part of the construct family
works; ✗ = no inference. A ✓ on Q2–Q4 and Q6–Q7 does not depend on `owl:sameAs`
support, which is tested separately in Q5.

| Query (construct) | GraphDB rdfsplus-opt | GraphDB owl2-ql-opt | GraphDB owl-max | GraphDB owl2-rl-opt | Jena transitive | Jena rdfs | Jena owl-micro | Jena owl-mini / owl |
|---|---|---|---|---|---|---|---|---|
| Q1 domain + subClassOf | ✗ | ◐ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Q2 subPropertyOf + range | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ |
| Q3 inverse / symmetric / transitive | ✓ | ◐ (no transitive) | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| Q4 equivalentClass / equivalentProperty | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| Q5 sameAs from IFP / functional property | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ |
| Q6 hasValue, someValuesFrom, allValuesFrom | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ◐ (no allValuesFrom) | ✓ |
| Q7 intersection, union | ✗ | ◐ (no union) | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ |
| Q8 property chain | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Q9 hasKey | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |

## Findings

1. **GraphDB `owl2-rl` is the only regime that passes every test.** It is
   the only one that applies the OWL 2 constructs (property chains, keys).
2. **Jena's `owl-mini` and `owl` match GraphDB `owl-max`** on Q1–Q7 and have
   the same gaps (Q8, Q9). Jena's OWL reasoners target OWL 1, so an
   OWL 2 RL-level result on Fuseki would need custom rules
   (`GenericRuleReasoner`) or an external reasoner.
3. **`owl-mini` and `owl` give identical answers here.** They differ only on
   rules that create blank nodes (e.g. minCardinality), which the suite does not
   exercise, so `owl-mini` is the cheaper choice for this level of expressivity.
4. **Approximate correspondence between the two stores:**

   | Jena reasoner | Closest GraphDB ruleset |
   |---|---|
   | `rdfs` | `rdfs` |
   | `owl-micro` | between `rdfsplus` and `owl-horst` (no sameAs, no allValuesFrom) |
   | `owl-mini` / `owl` | `owl-max` |

   The transitive reasoner only closes the class and property hierarchies and
   never types instances.
5. **RDFS behaviour differs.** Jena `rdfs` applies domain and range correctly,
   whereas GraphDB `rdfsplus-optimized` applies neither (Q1, Q2 empty) while
   handling inverse, symmetric and transitive properties.
6. **GraphDB `owl2-ql` goes beyond the QL profile in places and falls short in
   others.** It handles intersection on the subclass side, but not transitive
   properties or union.
7. **Answer sets also differ in vocabulary-level types.** Jena adds
   `rdfs:Resource` to every individual; the GraphDB OWL 2 rulesets add
   `owl:Thing`. Row counts therefore differ slightly even when the
   meaningful answers match.
8. **When reasoning happens:** GraphDB pays at load time. Fuseki pays at the
   first query: on the test KG about 0.35 s for `owl-mini` / `owl` against 0.04 s
   for `owl-micro`, then a few ms per query. The test KG is too small for these
   timings to say anything about scale.

## Implicit triples and consistency

| | GraphDB | Fuseki / Jena |
|---|---|---|
| Implicit triples on `university.ttl` | rdfsplus 193, owl-max 361, owl2-rl 1263, owl2-ql 1596 ([`implicit_report.md`](graphdb/results/implicit_report.md)) | pending: `fuseki/code/JenaReasoners.java` |
| Detection of the three cases in `inconsistent.ttl` | checked on commit, only with consistency checks enabled and a ruleset with consistency rules (see [GraphDB README](graphdb/README.md#consistency)) | pending: `JenaReasoners.java --validate-only` (`InfModel.validate()`, not available through the SPARQL endpoint) |

## Open items

- Run `JenaReasoners.java` on `university.ttl` and `inconsistent.ttl`.
- Add a `maxCardinality 1` test and a blank-node-creating test to separate
  `owl-max` from `owl-horst` and `owl-mini` from `owl`.
- Compare against a DL reasoner (e.g. HermiT, Konclude, or Openllet plugged
  into Jena) to isolate what needs disjunctive or existential reasoning.
