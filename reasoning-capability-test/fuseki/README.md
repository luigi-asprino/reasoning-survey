# Reasoning-capability tests — Apache Jena Fuseki

Runs the same test KG and query suite as the [GraphDB tests](../graphdb/README.md)
against Fuseki, one dataset per Jena reasoner, so the two reports can be compared
row by row. The inputs are read from `../graphdb/data/` (not copied).

## How reasoning differs from GraphDB

| | GraphDB | Fuseki / Jena |
|---|---|---|
| Configuration | ruleset chosen when the repository is created | `ja:InfModel` + `ja:reasoner` in the Fuseki assembler file, per dataset |
| Strategy | forward chaining, materialised in the store at load time | rule engine run in memory (forward + backward chaining) when the dataset is first queried |
| Built-in regimes | rdfs, rdfsplus, owl-horst, owl-max, owl2-ql, owl2-rl (+ custom `.pie`) | transitive, RDFS, OWL Micro, OWL Mini, OWL (+ custom rules via `GenericRuleReasoner`) |
| Implicit triples | `onto:implicit` pseudo-graph | not exposed; computed by `JenaReasoners.java` |
| Consistency | checked on commit, if enabled | `InfModel.validate()` through the Java API; not exposed by the endpoint |

The Jena OWL reasoners target OWL 1 (OWL Lite plus part of OWL DL), so OWL 2
constructs such as property chains (Q8) and keys (Q9) are not expected to fire.
For full OWL 2 DL, an external reasoner such as Openllet can be plugged into Jena;
that is not covered by these scripts.

## Contents

| Path | Description |
|---|---|
| `code/run_fuseki_tests.py` | Generates the Fuseki config (one dataset per reasoner), optionally starts Fuseki, runs Q1–Q9 and writes a side-by-side report. Reuses the query parsing and normalisation of `../graphdb/code/run_reasoning_tests.py`. |
| `code/JenaReasoners.java` | Runs the same reasoners through the Jena API: preparation time, implicit triples per predicate, consistency (`validate()`). |
| `results/fuseki-config.ttl` | Generated Fuseki configuration (rewritten on every run). |
| `results/fuseki_reasoning_report.md` / `.json` | Output of `run_fuseki_tests.py`. |

## Setup

1. Java 17 or later.
2. Download Apache Jena Fuseki 5.x (`apache-jena-fuseki-5.x.zip` from
   <https://jena.apache.org/download/>) and unzip it, e.g. in `~/opt/`.
   It contains the `fuseki-server` script and `fuseki-server.jar`.

## Query suite

Python 3, standard library only. Commands written as run from this folder.

```bash
# start Fuseki with the generated config, run Q1–Q9, stop Fuseki
python code/run_fuseki_tests.py --fuseki ~/opt/apache-jena-fuseki-5.6.0/fuseki-server

# subset of reasoners / queries
python code/run_fuseki_tests.py --fuseki ... --reasoners none rdfs owl --only Q1 Q2

# or run Fuseki yourself (e.g. to use its UI on http://localhost:3030)
python code/run_fuseki_tests.py --config-only
~/opt/apache-jena-fuseki-5.6.0/fuseki-server --config=results/fuseki-config.ttl
python code/run_fuseki_tests.py
```

Datasets: `none`, `transitive`, `rdfs`, `owl-micro`, `owl-mini`, `owl` and
`compiled`, each at `http://localhost:3030/<name>/sparql`. Q10 (GraphDB's
`onto:implicit`) is skipped; see below.

`compiled` is a rule profile generated from the test KG by
[`jena-rule-profile/code/compile_rules.py`](../../jena-rule-profile/README.md)
(with `--sameas`; needs rdflib), written to `results/compiled.rules`. Pass
`--rules FILE` to use another profile.

## Implicit triples and consistency

```bash
FUSEKI_JAR=~/opt/apache-jena-fuseki-5.6.0/fuseki-server.jar

java -cp $FUSEKI_JAR code/JenaReasoners.java ../graphdb/data/university.ttl > results/jena_reasoners_report.md
java -cp $FUSEKI_JAR code/JenaReasoners.java --validate-only ../graphdb/data/inconsistent.ttl > results/jena_consistency_report.md
```

Options: `--reasoners rdfs,owl` (subset), `--top 0` (all predicates). The
preparation time is the closest analogue of GraphDB's materialisation at load
time; the same command on ECMO (+ DUL) gives the loading-time comparison.

## Findings so far

Query suite on `university.ttl` (Fuseki 5, in-memory datasets); compare with
the [GraphDB findings](../graphdb/README.md#findings-so-far).

| Query | none | transitive | rdfs | owl-micro | owl-mini / owl | GraphDB owl2-rl |
|---|---|---|---|---|---|---|
| Q1 domain + subClassOf | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Q2 subPropertyOf + range | ✗ | ✗ | ✓ | ✓ | ✓ (+ sameAs copies) | ✓ |
| Q3 inverse / symmetric / transitive | ✗ | ✗ | ✗ | ✓ | ✓ (+ sameAs copies) | ✓ |
| Q4 equivalentClass / equivalentProperty | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Q5 sameAs from IFP / functional | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Q6 hasValue, someValuesFrom, allValuesFrom | ✗ | ✗ | ✗ | partial (no allValuesFrom) | ✓ | ✓ |
| Q7 intersection, union | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Q8 property chain | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| Q9 hasKey | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

- `transitive` only closes the class and property hierarchies; it never types
  instances, so it adds nothing to these queries.
- `rdfs` applies domain and range correctly (unlike GraphDB's
  `rdfsplus-optimized`), but has no inverse, symmetric or transitive properties.
- `owl-micro` sits between GraphDB's rdfsplus and owl-horst: it handles
  equivalence, inverse/symmetric/transitive properties, hasValue,
  someValuesFrom, intersection and union, but derives no `owl:sameAs` and does
  not apply allValuesFrom.
- `owl-mini` and `owl` give identical answers, the same as GraphDB `owl-max`
  on Q1–Q7. They differ only on rules that create blank nodes
  (minCardinality, someValuesFrom as a superclass), which the suite does not test.
- No Jena reasoner supports OWL 2 property chains or keys (Q8, Q9). On Q9,
  `owl-mini`/`owl` only return the reflexive `dario owl:sameAs dario`.
- Jena also returns `rdfs:Resource` among the inferred types.
- Reasoning happens at the first query: on the test KG this took about 0.35 s
  for `owl-mini`/`owl` against 0.04 s for `owl-micro`; later queries take a few ms.
