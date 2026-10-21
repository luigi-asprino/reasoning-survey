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

Datasets: `none`, `transitive`, `rdfs`, `owl-micro`, `owl-mini`, `owl`, each at
`http://localhost:3030/<name>/sparql`. Q10 (GraphDB's `onto:implicit`) is
skipped; see below.

## Implicit triples and consistency

```bash
FUSEKI_JAR=~/opt/apache-jena-fuseki-5.6.0/fuseki-server.jar

java -cp $FUSEKI_JAR code/JenaReasoners.java ../graphdb/data/university.ttl > results/jena_reasoners_report.md
java -cp $FUSEKI_JAR code/JenaReasoners.java --validate-only ../graphdb/data/inconsistent.ttl > results/jena_consistency_report.md
```

Options: `--reasoners rdfs,owl` (subset), `--top 0` (all predicates). The
preparation time is the closest analogue of GraphDB's materialisation at load
time; the same command on ECMO (+ DUL) gives the loading-time comparison.
