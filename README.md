# GraphDB reasoning test-bed

A small university knowledge graph and a query suite for comparing what the
GraphDB entailment regimes (rulesets) actually infer, together with LaTeX notes
relating those regimes to Description Logic families and OWL 2 profiles.

## Contents

| Path | Description |
|---|---|
| `university.ttl` | Test ontology + data. Each axiom block is tagged with the minimum ruleset expected to fire it (RDFS → OWL 2 RL). |
| `inconsistent.ttl` | Three independent inconsistencies (disjointness, functional property + `owl:differentFrom`, disjointness via inferred range). Load one at a time, with consistency checks enabled. |
| `queries.rq` | Queries Q1–Q10, one construct family each, with expected results in the comments. |
| `run_reasoning_tests.py` | Runs `queries.rq` against several repositories and writes a side-by-side comparison. |
| `reasoning_report.md` / `.json` | Output of the last run. |
| `notes/dl-owl-expressivity.tex` | Notes on DL naming, OWL 2 profiles, GraphDB rulesets as Horn fragments, empirical results, and available reasoners. |

## Setup

1. Start GraphDB on `http://localhost:7200`.
2. Create one repository per ruleset, with ids starting with `reasoning-test-`
   (the script discovers them by prefix). Used so far:

   | Repository | Ruleset |
   |---|---|
   | `reasoning-test-rdfs-plus-opt` | `rdfsplus-optimized` |
   | `reasoning-test-horst` | `owl-horst-optimized` |
   | `reasoning-test-owl-max` | `owl-max-optimized` |
   | `reasoning-test-owl2-ql-opt` | `owl2-ql-optimized` |

   Uncheck **Disable owl:sameAs**, otherwise Q5 and Q9 are always empty.

## Usage

Python 3, standard library only.

```bash
python run_reasoning_tests.py --load          # clear each repo, load university.ttl, run all queries
python run_reasoning_tests.py                 # re-run queries on the loaded data
python run_reasoning_tests.py --only Q1 Q7    # subset of queries
python run_reasoning_tests.py --no-infer      # explicit statements only (baseline)
python run_reasoning_tests.py --repos reasoning-test-horst reasoning-test-owl-max
python run_reasoning_tests.py --load --data inconsistent.ttl   # expect load failures
```

The script prints each repository's ruleset and `disableSameAs` setting,
normalises blank-node labels and IRIs so results are comparable, and lists what
each repository is missing relative to the union of all results (skipped for
aggregate queries).

## Findings so far

- `rdfsplus-optimized` applies neither `rdfs:domain` nor `rdfs:range`
  (Q1, Q2 empty), although inverse, symmetric and transitive properties work.
  Not explained by the documented optimisations — to be confirmed on the
  non-optimised ruleset.
- `owl-horst` handles `owl:intersectionOf` in both directions (beyond textbook pD\*).
- `owl-max` differs from `owl-horst` here only on `owl:unionOf`.
- `owl2-ql` is more permissive than the OWL 2 QL profile (subclass-side
  intersection) and materialises far more (1596 implicit triples vs 193–361).
- Q8 (property chains) and Q9 (`owl:hasKey`) are untested: no OWL 2 RL repository yet.

## Next steps

- Add `reasoning-test-owl2-rl` (and a plain `reasoning-test-rdfs`).
- Re-run the RDFS-Plus domain/range test on the non-optimised ruleset.
- Add a `maxCardinality 1` test to separate OWL-Max from OWL-Horst further.
- Compare against a DL reasoner (HermiT / Konclude) to isolate what needs
  disjunctive or existential reasoning.

## Building the notes

```bash
cd notes && pdflatex dl-owl-expressivity.tex && pdflatex dl-owl-expressivity.tex
```
