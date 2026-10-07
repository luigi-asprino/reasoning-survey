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
| `benchmark_rulesets.py` | Measures how each ruleset affects loading time and materialisation size. |
| `ecmo-graphdb-benchmark.sh` | Runs the loading-time benchmark on the ECMO ontology. |
| `notes/dl-owl-expressivity.tex` | Notes on DL naming, OWL 2 profiles, GraphDB rulesets as Horn fragments, empirical results, and available reasoners. |

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

## Loading-time benchmark

`benchmark_rulesets.py` measures what each entailment regime costs at load
time. GraphDB materialises inferences on commit, so the time a load takes
includes the whole forward-chaining step. The script repeats the following for
every ruleset:

1. Create a fresh repository `bench-ruleset-<ruleset>`.
2. Load the ontology files, if any, timing them separately.
3. Load the data files.
4. Record explicit, inferred and total statement counts.
5. Delete the repository.

The `reasoning-test-*` repositories are never touched. Standard library only.

The `rdfsplus` rulesets are excluded because they don't apply `rdfs:domain`
and `rdfs:range` (see below).

```bash
python benchmark_rulesets.py                       # university.ttl, 11 built-in rulesets (all but rdfsplus*), 1 warm-up + 3 runs
python benchmark_rulesets.py --ontology onto.ttl --data data1.ttl data2.nt.gz -n 5
python benchmark_rulesets.py --rulesets empty rdfs-optimized owl-horst-optimized owl2-rl-optimized --keep
python benchmark_rulesets.py --disable-sameas      # GraphDB's own default; affects horst/max/rl
python benchmark_rulesets.py --check-inconsistencies
```

Each run is written to a CSV (`benchmark_rulesets_<timestamp>.csv`, or set it
with `-o`). The script then prints the median load time, standard deviation,
slowdown compared with `empty`, and the ratio of inferred to explicit
statements for each ruleset. owl:sameAs handling is enabled by default, as in
the test repositories.

`university.ttl` loads in milliseconds, so use a larger dataset to get
meaningful timings. Gzipped files are decompressed on the fly. A `.owl`/`.rdf`/`.xml` file that
fails to parse as RDF/XML is retried as Turtle (DUL.owl is Turtle); the failed
attempt is excluded from the timing. The repository
config uses the GraphDB 10.x vocabulary.

### ECMO

`ecmo-graphdb-benchmark.sh` runs the benchmark on the ECMO release in
`../ecmo-0.3.1-dl42-patched`. It loads every ECMO module and the alignments
as the ontology, and the unit-test case fixtures as data (`--no-data` to skip).
DUL and d0 are not loaded unless you pass `--dul`: GraphDB doesn't follow
`owl:imports`, so the script then downloads them once into `ecmo-deps/`.

```bash
./ecmo-graphdb-benchmark.sh                          # sameAs on and off, with data, 10 runs
./ecmo-graphdb-benchmark.sh --sameas off --no-data   # one mode, ontology only
./ecmo-graphdb-benchmark.sh --dul                    # also load DUL and d0
./ecmo-graphdb-benchmark.sh -n 1 --rulesets empty rdfs-optimized owl2-ql-optimized owl-horst-optimized owl-max-optimized owl2-rl-optimized 
```

ECMO contains about 3.7k `owl:sameAs` links, mostly in `ecmo-ph.ttl`, so it is
worth comparing both sameAs modes. Results go to
`ecmo_benchmark_sameas-<on|off>_<data|nodata>[_dul]_<timestamp>.csv`.

## Findings so far

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
  more (QL 1596, RL 1263 implicit triples vs 193–361).

## Next steps

- Add a plain `reasoning-test-rdfs` repository.
- Re-run the RDFS-Plus domain/range test on the non-optimised ruleset.
- Add a `maxCardinality 1` test to separate OWL-Max from OWL-Horst further.
- Compare against a DL reasoner (HermiT / Konclude) to isolate what needs
  disjunctive or existential reasoning.

## Building the notes

```bash
cd notes && pdflatex dl-owl-expressivity.tex && pdflatex dl-owl-expressivity.tex
```
