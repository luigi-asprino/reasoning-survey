# Results — loading-time tests, GraphDB

One CSV per benchmark run, one row per (ruleset, repetition).

## Columns

| Column | Meaning |
|---|---|
| `ruleset` | GraphDB ruleset |
| `run` | Repetition number (warm-up runs first) |
| `warmup` | `True` for warm-up runs, excluded from the summary |
| `onto_load_s`, `data_load_s`, `total_load_s` | Load time in seconds, including materialisation |
| `explicit`, `inferred`, `total` | Statement counts after loading |
| `inferred_ratio` | `inferred / explicit` |
| `consistent` | With consistency checks on: `True`, or `False` if the load was rejected |
| `error` | Error or consistency-violation message |

## File names

| Pattern | Produced by |
|---|---|
| `benchmark_rulesets_<timestamp>.csv` | `../code/benchmark_rulesets.py` |
| `ecmo_benchmark_sameas-<on\|off>_<data\|nodata>[_<dul variant>][_consistency]_<timestamp>.csv` | `../code/ecmo-graphdb-benchmark.sh` |
| `settingN-<original name>.csv` | ECMO runs renamed by hand to keep them |

The first two patterns are git-ignored; rename a run to `settingN-…` to track it.

| Setting | sameAs | Data | DUL | Consistency |
|---|---|---|---|---|
| `setting1` | off | no | no | no |
| `setting2` | off | no | no | yes |
| `setting3` | off | no | DUL-lite | no |
| `setting4` | off | no | DUL-lite | yes |
