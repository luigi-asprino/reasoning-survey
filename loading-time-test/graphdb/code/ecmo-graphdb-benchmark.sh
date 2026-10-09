#!/usr/bin/env bash
# Benchmark GraphDB rulesets on the ECMO ontology (wrapper around benchmark_rulesets.py).
#
# Loads all ECMO modules + alignments as the ontology and, optionally, the
# unit-test case fixtures as data and the external imports DUL + d0 (GraphDB
# does not follow owl:imports, so with --dul they are downloaded once and loaded).
#
# Usage: ./ecmo-graphdb-benchmark.sh [options] [-- extra benchmark_rulesets.py args]
#
#   --sameas on|off|both   owl:sameAs handling in the benchmark repos (default: both)
#   --data | --no-data     also load the case fixtures as data (default: --data)
#   --dul | --no-dul       also load DUL and d0 as ontology (default: --no-dul)
#   --dul-lite             like --dul, but dul:associatedWith is neither transitive
#                          nor symmetric (../data/dul-variants/DUL-lite.ttl)
#   --dul-flat             like --dul, but no DUL property is transitive or
#                          symmetric (../data/dul-variants/DUL-flat.ttl)
#   --dul-file FILE        like --dul, but load FILE instead of DUL
#   --consistency          enable GraphDB consistency checks; an inconsistent load
#                          is reported as INCONSISTENT with the violated rule
#   --ecmo DIR             ECMO release folder (default: JRC/ecmo/0.3.1_audited)
#   -n N                   measured repetitions per ruleset (default: 10)
#   --rulesets R1 R2 ...   rulesets to test (default: all but rdfsplus*)
#   -h, --help             show this help
#
# Examples:
#   ./ecmo-graphdb-benchmark.sh
#   ./ecmo-graphdb-benchmark.sh --sameas off --no-data
#   ./ecmo-graphdb-benchmark.sh --dul
#   ./ecmo-graphdb-benchmark.sh --dul-lite --rulesets owl-horst-optimized owl2-rl-optimized
#   ./ecmo-graphdb-benchmark.sh --consistency --sameas on -n 1 --rulesets owl2-rl-optimized
#   ./ecmo-graphdb-benchmark.sh -n 5 --rulesets empty rdfs-optimized owl2-rl-optimized
#   ./ecmo-graphdb-benchmark.sh -- --url http://other-host:7200 --warmup 0
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"          # .../loading-time-test/graphdb/code
DATA_DIR="$(cd "$HERE/../data" && pwd)"
RESULTS_DIR="$(cd "$HERE/../results" && pwd)"
ECMO="$HERE/../../../../ecmo/0.3.1_audited"     # JRC/ecmo, next to the reasoning repo
SAMEAS="both"
WITH_DATA=1
WITH_DUL=0
DUL_FILE=""      # empty = original DUL (downloaded)
DUL_TAG="dul"
CONSISTENCY=0
REPS=10
RULESETS=()
EXTRA=()

usage() { sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --sameas)  SAMEAS="${2:-}"; shift 2 ;;
    --data)    WITH_DATA=1; shift ;;
    --no-data) WITH_DATA=0; shift ;;
    --dul)      WITH_DUL=1; DUL_FILE=""; DUL_TAG="dul"; shift ;;
    --no-dul)   WITH_DUL=0; shift ;;
    --dul-lite) WITH_DUL=1; DUL_FILE="$DATA_DIR/dul-variants/DUL-lite.ttl"; DUL_TAG="dul-lite"; shift ;;
    --dul-flat) WITH_DUL=1; DUL_FILE="$DATA_DIR/dul-variants/DUL-flat.ttl"; DUL_TAG="dul-flat"; shift ;;
    --dul-file) WITH_DUL=1; DUL_FILE="${2:-}"; DUL_TAG="dul-$(basename "${2:-custom}" | sed 's/\.[^.]*$//')"; shift 2 ;;
    --consistency) CONSISTENCY=1; shift ;;
    --ecmo)    ECMO="${2:-}"; shift 2 ;;
    -n)        REPS="${2:-}"; shift 2 ;;
    --rulesets)
      shift
      while [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; do RULESETS+=("$1"); shift; done
      [ "${#RULESETS[@]}" -gt 0 ] || { echo "--rulesets needs at least one ruleset" >&2; exit 1; } ;;
    -h|--help) usage 0 ;;
    --)        shift; EXTRA=("$@"); break ;;
    *)         echo "Unknown option: $1" >&2; usage 1 ;;
  esac
done

case "$SAMEAS" in
  on|off|both) ;;
  *) echo "--sameas must be on, off or both (got '$SAMEAS')" >&2; exit 1 ;;
esac
[ -d "$ECMO" ] || { echo "ECMO folder not found: $ECMO" >&2; exit 1; }
ECMO="$(cd "$ECMO" && pwd)"

# --- external imports (DUL, d0) -------------------------------------------------
DEPS="$DATA_DIR/ecmo-deps"
mkdir -p "$DEPS"
fetch() {  # url file
  if [ ! -s "$DEPS/$2" ]; then
    echo "Downloading $1"
    curl -fsSL -o "$DEPS/$2" "$1"
  fi
}

# --- files ------------------------------------------------------------------------
shopt -s nullglob
ONTO=()
if [ "$WITH_DUL" -eq 1 ]; then
  fetch http://www.ontologydesignpatterns.org/ont/d0.owl d0.owl
  if [ -z "$DUL_FILE" ]; then
    fetch http://www.ontologydesignpatterns.org/ont/dul/DUL.owl DUL.owl
    DUL_FILE="$DEPS/DUL.owl"
  fi
  [ -f "$DUL_FILE" ] || { echo "DUL file not found: $DUL_FILE" >&2; exit 1; }
  ONTO+=("$DUL_FILE" "$DEPS/d0.owl")
fi
ONTO+=("$ECMO"/ecmo-*.ttl "$ECMO"/0.3.1-alignments/*.ttl)
DATA=()
if [ "$WITH_DATA" -eq 1 ]; then
  for f in ecmo-ebola-case.ttl ecmo-hantavirus-case.ttl \
           ecmo-coreference-pattern-fixture.ttl ecmo-phsm-fixtures.ttl; do
    [ -f "$ECMO/0.3.1-unittests/$f" ] && DATA+=("$ECMO/0.3.1-unittests/$f")
  done
fi
echo "Ontology files: ${#ONTO[@]}   data files: ${#DATA[@]}   DUL/d0: $([ "$WITH_DUL" -eq 1 ] && echo "$(basename "$DUL_FILE")" || echo no)   repetitions: $REPS"

list_files() {  # label file...
  local label="$1"; shift
  echo "$label ($#):"
  local i=1 f
  for f in "$@"; do
    local full; full="$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
    printf '  %3d. %s  (%s KB)\n' "$i" "$full" "$(( $(wc -c < "$f") / 1024 ))"
    i=$((i + 1))
  done
}
list_files "Ontology files" "${ONTO[@]}"
if [ "${#DATA[@]}" -gt 0 ]; then list_files "Data files" "${DATA[@]}"; else echo "Data files: none"; fi

# --- runs -------------------------------------------------------------------------
STAMP="$(date +%Y%m%d_%H%M%S)"
DATA_TAG=$([ "$WITH_DATA" -eq 1 ] && echo data || echo nodata)
[ "$WITH_DUL" -eq 1 ] && DATA_TAG="${DATA_TAG}_${DUL_TAG}"
[ "$CONSISTENCY" -eq 1 ] && DATA_TAG="${DATA_TAG}_consistency"
MODES=$([ "$SAMEAS" = both ] && echo "on off" || echo "$SAMEAS")

for mode in $MODES; do
  flag=$([ "$mode" = on ] && echo --no-disable-sameas || echo --disable-sameas)
  out="$RESULTS_DIR/ecmo_benchmark_sameas-${mode}_${DATA_TAG}_${STAMP}.csv"
  echo
  echo "=== $(date +%H:%M:%S) start loading: owl:sameAs $mode, ${DATA_TAG//_/, } ==="
  # --data is always passed (possibly with no files), otherwise
  # benchmark_rulesets.py falls back to university.ttl
  args=(--ontology "${ONTO[@]}" -n "$REPS" "$flag" -o "$out" --data ${DATA[@]+"${DATA[@]}"})
  [ "${#RULESETS[@]}" -gt 0 ] && args+=(--rulesets "${RULESETS[@]}")
  [ "$CONSISTENCY" -eq 1 ] && args+=(--check-inconsistencies)
  python3 "$HERE/benchmark_rulesets.py" "${args[@]}" ${EXTRA[@]+"${EXTRA[@]}"}
done
