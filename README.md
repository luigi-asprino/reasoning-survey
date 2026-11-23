# Triplestore reasoning test-bed

Experiments on what SPARQL endpoints with built-in reasoning actually infer, and
what that reasoning costs at load time, together with LaTeX notes relating the
entailment regimes to Description Logic families and OWL 2 profiles.

Tested so far: GraphDB and Apache Jena Fuseki (reasoning capability and
loading time). A cross-triplestore summary of the reasoning-capability
results is in [`reasoning-capability-test/SUMMARY.md`](reasoning-capability-test/SUMMARY.md). Each test family has one
subfolder per triplestore, so others can be added side by side.

## Layout

```
reasoning/
├── data/                          shared inputs: DUL versions, d0
├── notes/                         LaTeX notes and slides on DL/OWL expressivity
├── reasoning-capability-test/     what each entailment regime infers
│   ├── graphdb/
│   │   ├── code/
│   │   ├── data/
│   │   └── results/
│   └── fuseki/
├── loading-time-test/             how much each entailment regime costs at load time
│   ├── graphdb/
│   │   ├── code/
│   │   └── results/
│   └── fuseki/
└── jena-rule-profile/             an ontology-specific Jena rule profile (ECMO)
```

| Folder | Content |
|---|---|
| [`data/`](data/README.md) | DUL, its lighter variants, DUL 4.3 and d0, shared by all tests. |
| [`notes/`](notes/README.md) | Notes on DL naming, OWL 2 profiles, GraphDB rulesets as Horn fragments, empirical results and available reasoners. |
| [`reasoning-capability-test/`](reasoning-capability-test/README.md) | Test KG and query suite to compare entailment regimes (GraphDB, Fuseki); consistency checks; analysis of the ECMO + DUL inconsistencies. |
| [`loading-time-test/`](loading-time-test/README.md) | Loading-time and materialisation-size benchmarks, on the test KG and on the ECMO ontology. |
| [`jena-rule-profile/`](jena-rule-profile/README.md) | Compiles an ontology into forward Jena rules specialised to its axioms (OWL 2 RL subset), so Fuseki can reason on ECMO + DUL; includes the ECMO 0.3.1 profile. |

## Conventions

- Every `<test>/<triplestore>/` folder has `code/` (scripts) and `results/`
  (outputs, reports and analyses), plus `data/` when it has inputs of its own.
  Inputs shared across tests (DUL versions, d0) are in the top-level `data/`.
- Default paths in the scripts are resolved relative to the script itself, so
  every command works from any directory. By default, inputs are read from
  `../data` and outputs are written to `../results`.
- Each folder has a README. The one in `<test>/<triplestore>/` documents setup,
  usage and findings for that triplestore.

### Dependencies between the two test families

These are kept explicit instead of duplicating code or data:

- `reasoning-capability-test/graphdb/code/compare_implicit.py` reuses the
  GraphDB REST client defined in
  `loading-time-test/graphdb/code/benchmark_rulesets.py`.
- `loading-time-test/graphdb/code/benchmark_rulesets.py` uses
  `reasoning-capability-test/graphdb/data/university.ttl` as its default
  (smoke-test) data.
- DUL, its variants and d0 live in the shared [`data/`](data/README.md) folder, used
  by both benchmarks (GraphDB and Fuseki), `check_disjointness.py` and the Jena
  rule profile.

### External data

The ECMO experiments read the ECMO release from `../ecmo/0.3.1_audited`, i.e.
the `ecmo` repository next to this one (`JRC/ecmo`). Both
`ecmo-graphdb-benchmark.sh` and `check_disjointness.py` accept `--ecmo DIR` to
use another release.

## Adding a triplestore

1. Create `reasoning-capability-test/<store>/` and/or
   `loading-time-test/<store>/`, each with `code/`, `data/`, `results/` and a
   `README.md`, following the GraphDB folders.
2. Reuse the GraphDB test inputs (`university.ttl`, `queries.rq`,
   `inconsistent.ttl`) where possible, so results stay comparable.
3. Add the new folder to the tables in the README of the test family.

## Requirements

- Python 3. The GraphDB scripts use the standard library only;
  `check_disjointness.py` and `make_dul_variants.py` need `rdflib`.
- A GraphDB 10.x instance on `http://localhost:7200`.
- `pdflatex` to build the notes.
