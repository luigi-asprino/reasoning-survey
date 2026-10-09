# Reasoning-capability tests — GraphDB

Compares what the GraphDB rulesets (entailment regimes) infer on the test KG,
and checks consistency detection.

## Contents

| Path | Description |
|---|---|
| `code/run_reasoning_tests.py` | Runs `data/queries.rq` against several repositories and writes a side-by-side comparison. |
| `code/compare_implicit.py` | Explains why two rulesets materialise a different number of implicit triples. |
| `code/check_disjointness.py` | Lists every disjointness violation in ECMO + DUL + case data, with derivations (needs rdflib). |
| `data/university.ttl` | Test ontology + data. Each axiom block is tagged with the minimum ruleset expected to fire it (RDFS → OWL 2 RL). |
| `data/queries.rq` | Queries Q1–Q10, one construct family each, with expected results in the comments. |
| `data/inconsistent.ttl` | Three independent inconsistencies. Load one at a time, with consistency checks enabled. |
| `results/reasoning_report.md` / `.json` | Output of the last `run_reasoning_tests.py` run. |
| `results/implicit_report.md` | Output of the last `compare_implicit.py` run (owl2-ql vs owl2-rl on `university.ttl`). |
| `results/ecmo-inconsistencies.md` | Why ECMO 0.3.1 + DUL + the case fixtures is inconsistent, and a verified fix set. |

All default paths are relative to the scripts, so the commands below work from
any directory. They are written as run from this folder.

## Setup

1. Start GraphDB on `http://localhost:7200`.
2. Create one repository per ruleset, with ids starting with `reasoning-test-`
   (the script discovers them by prefix). Used so far:

   | Repository | Ruleset |
   |---|---|
   | `reasoning-test-rdfs-plus-opt` | `rdfsplus-optimized` |
   | `reasoning-test-owl-max` | `owl-max-optimized` |
   | `reasoning-test-owl2-ql-opt` | `owl2-ql-optimized` |
   | `reasoning-test-rl-opt` | `owl2-rl-optimized` |

   An earlier run also used `reasoning-test-horst` (`owl-horst-optimized`);
   its results are recorded in the notes.

   Uncheck **Disable owl:sameAs**, otherwise Q5 and Q9 are always empty.

## Query suite

Python 3, standard library only.

```bash
python code/run_reasoning_tests.py --load          # clear each repo, load university.ttl, run all queries
python code/run_reasoning_tests.py                 # re-run queries on the loaded data
python code/run_reasoning_tests.py --only Q1 Q7    # subset of queries
python code/run_reasoning_tests.py --no-infer      # explicit statements only (baseline)
python code/run_reasoning_tests.py --repos reasoning-test-horst reasoning-test-owl-max
python code/run_reasoning_tests.py --load --data data/inconsistent.ttl   # expect load failures
```

The script prints each repository's ruleset and `disableSameAs` setting,
normalises blank-node labels and IRIs so results are comparable, and lists what
each repository is missing relative to the union of all results (skipped for
aggregate queries). The report goes to `results/reasoning_report.md` (+ `.json`);
change it with `--report`.

## Implicit-triple comparison

`compare_implicit.py` creates a temporary repository for each of two rulesets
(`implicit-<ruleset>`), loads the data, fetches every implicit triple
(`FROM onto:implicit`) and reports the counts per predicate and per class,
plus the triples only one ruleset infers. It reuses the GraphDB client of
[`loading-time-test/graphdb/code/benchmark_rulesets.py`](../../loading-time-test/graphdb/code/benchmark_rulesets.py).

```bash
python code/compare_implicit.py                     # university.ttl, owl2-ql-optimized vs owl2-rl-optimized
python code/compare_implicit.py --rulesets owl-horst-optimized owl2-rl-optimized
python code/compare_implicit.py --data onto.ttl data.ttl --keep --report results/implicit_ecmo.md
```

## Consistency

GraphDB checks consistency only when the repository is created with
consistency checks enabled, and only rulesets that contain consistency rules
(owl-horst, owl-max, owl2-ql, owl2-rl) can detect anything. GraphDB then
rejects the commit that fires the first rule.

To check detection on the three test cases:

```bash
python ../../loading-time-test/graphdb/code/benchmark_rulesets.py \
    --data data/inconsistent.ttl --check-inconsistencies --rulesets owl2-rl-optimized
```

### ECMO

Since GraphDB stops at the first violation, `check_disjointness.py` computes
the OWL 2 RL type inferences that matter for disjointness and lists all
violations, grouped by the ECMO → DUL alignments involved. Defaults: ECMO from
`JRC/ecmo/0.3.1_audited`, `DUL-lite.ttl` and `d0.owl` from
`loading-time-test/graphdb/data/`.

```bash
python code/check_disjointness.py                   # ECMO + DUL-lite + case fixtures
python code/check_disjointness.py --no-data         # ontology only
python code/check_disjointness.py --examples 3      # more derivations per group
```

The analysis and the verified fix set are in
[`results/ecmo-inconsistencies.md`](results/ecmo-inconsistencies.md).

## Findings so far

- ECMO 0.3.1 + DUL + the Ebola/Hondius case fixtures is inconsistent: 31
  individuals fall in disjoint DUL classes (Event/Object, Object/Quality), caused
  by five groups of alignments in `ecmo-property-alignments.ttl`. Details and a
  verified fix set in [`results/ecmo-inconsistencies.md`](results/ecmo-inconsistencies.md).
- `rdfsplus-optimized` applies neither `rdfs:domain` nor `rdfs:range`
  (Q1, Q2 empty), although inverse, symmetric and transitive properties work.
  `owl2-rl-optimized` applies them correctly, so the problem is specific to
  that ruleset — to be confirmed on the non-optimised `rdfsplus`.
- `owl-horst` handles `owl:intersectionOf` in both directions (beyond textbook pD\*).
- `owl-max` differs from `owl-horst` here only on `owl:unionOf`.
- `owl2-rl` passes every test: it matches `owl-max` on Q1–Q7 and is the only
  ruleset firing property chains (Q8) and `owl:hasKey` (Q9). It also classifies
  via an equivalence with an existential, which lies outside the RL profile.
- `owl2-ql` is more permissive than the OWL 2 QL profile (subclass-side
  intersection).
- Both OWL 2 rulesets type every individual as `owl:Thing` and materialise far
  more (QL 1596, RL 1263 implicit triples vs 193–361); see
  [`results/implicit_report.md`](results/implicit_report.md).

## Next steps

- Add a plain `reasoning-test-rdfs` repository.
- Re-run the RDFS-Plus domain/range test on the non-optimised ruleset.
- Add a `maxCardinality 1` test to separate OWL-Max from OWL-Horst further.
- Compare against a DL reasoner (HermiT / Konclude) to isolate what needs
  disjunctive or existential reasoning.
