#!/usr/bin/env bash
# Blind-evaluate a packed pilot on main questions (Luna / writer deployment).
# Usage:
#   scripts/evaluate-pilot.sh
#   scripts/evaluate-pilot.sh --local-dir data/packed/pilot_v2.jsonl --label v2
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOCAL_DIR="data/packed/pilot_v2.jsonl"
LABEL="v2"
SOLVER_PROVIDER="azure"
CONFIG="pilot_v2"
LIMIT=""
MAX_ACCURACY="0.30"
OUTPUT_ROOT="data"
SKIP_SNAPSHOT=0

usage() {
  cat <<'EOF'
Evaluate main-question hardness on a packed JSONL (after assess has passed).

Options:
  --local-dir PATH        Packed JSONL (default: data/packed/pilot_v2.jsonl)
  --label NAME            Snapshot suffix for data/packed/luna_eval_metrics_<label>.json
                          (default: v2)
  --solver-provider NAME  azure|glm (default: azure)
  --config NAME           Dataset config label in metrics (default: pilot_v2)
  --limit N               Optional row cap (default: all rows)
  --max-accuracy F        Development hardness threshold (default: 0.30)
  --output-root DIR       Eval artifact root (default: data)
  --skip-snapshot         Do not copy metrics into data/packed/
  -h, --help              Show this help

Writes:
  data/processed/evals/<eval_id>/{metrics.json,predictions.jsonl}
  data/packed/luna_eval_metrics_<label>.json   (unless --skip-snapshot)

Exit codes:
  0  main_accuracy <= max-accuracy (development hardness gate passed)
  2  hardness gate failed
  other  runner/transport failure

Protocol: run assess first; hardness cannot compensate for failed narration/diversity.
See .agents/skills/dataset-quality/SKILL.md.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-dir) LOCAL_DIR="$2"; shift 2 ;;
    --label) LABEL="$2"; shift 2 ;;
    --solver-provider) SOLVER_PROVIDER="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --max-accuracy) MAX_ACCURACY="$2"; shift 2 ;;
    --output-root) OUTPUT_ROOT="$2"; shift 2 ;;
    --skip-snapshot) SKIP_SNAPSHOT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ ! -f "${LOCAL_DIR}" ]]; then
  echo "error: packed JSONL not found: ${LOCAL_DIR}" >&2
  exit 1
fi

METRICS_SNAPSHOT="${OUTPUT_ROOT}/packed/luna_eval_metrics_${LABEL}.json"

# Prefer assessing when a sibling quality metrics file is absent — warn only.
PACK_STEM="$(basename "${LOCAL_DIR}" .jsonl)"
QUALITY_METRICS="$(dirname "${LOCAL_DIR}")/${PACK_STEM}_quality_metrics.json"
if [[ ! -f "${QUALITY_METRICS}" ]]; then
  echo "warning: ${QUALITY_METRICS} missing; run assess before hardness when possible." >&2
fi

if [[ -z "${LIMIT}" ]]; then
  LIMIT="$(grep -cve '^[[:space:]]*$' "${LOCAL_DIR}" || true)"
  if [[ -z "${LIMIT}" || "${LIMIT}" -eq 0 ]]; then
    echo "error: no rows in ${LOCAL_DIR}" >&2
    exit 1
  fi
fi

echo "==> evaluate main-only ${LOCAL_DIR} (solver=${SOLVER_PROVIDER}, limit=${LIMIT})"
eval_args=(
  evaluate
  --local-dir "${LOCAL_DIR}"
  --solver-provider "${SOLVER_PROVIDER}"
  --config "${CONFIG}"
  --output-root "${OUTPUT_ROOT}"
  --max-accuracy "${MAX_ACCURACY}"
  --limit "${LIMIT}"
  --main-only
)

# Capture JSON report from stdout while preserving exit code for hardness gate.
set +e
report="$(uv run cogito-mill "${eval_args[@]}")"
eval_code=$?
set -e
printf '%s\n' "${report}"

artifact_dir="$(
  printf '%s\n' "${report}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("artifact_dir",""))' 2>/dev/null || true
)"

if [[ "${SKIP_SNAPSHOT}" -eq 0 ]]; then
  if [[ -n "${artifact_dir}" && -f "${artifact_dir}/metrics.json" ]]; then
    mkdir -p "$(dirname "${METRICS_SNAPSHOT}")"
    cp "${artifact_dir}/metrics.json" "${METRICS_SNAPSHOT}"
    echo "snapshot: ${METRICS_SNAPSHOT}"
  else
    # Fallback: write the printed report (may lack artifact_dir on failure paths).
    mkdir -p "$(dirname "${METRICS_SNAPSHOT}")"
    printf '%s\n' "${report}" >"${METRICS_SNAPSHOT}"
    echo "snapshot (stdout): ${METRICS_SNAPSHOT}"
  fi
fi

if [[ "${eval_code}" -eq 0 ]]; then
  echo "hardness development gate PASSED (main_accuracy <= ${MAX_ACCURACY})"
elif [[ "${eval_code}" -eq 2 ]]; then
  echo "hardness development gate FAILED (main_accuracy > ${MAX_ACCURACY})" >&2
else
  echo "evaluate failed (exit ${eval_code})" >&2
fi

echo "Append results to docs/engineering/assessments/pilot-quality-iterations.md"
exit "${eval_code}"
