#!/usr/bin/env bash
# Blind-evaluate an assessed packed dataset on main questions.
# Usage:
#   scripts/evaluate-pilot.sh
#   scripts/evaluate-pilot.sh --local-dir data/packed/pilot_v2.jsonl --label v2
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOCAL_DIR=""
LABEL=""
SOLVER_PROVIDER="azure"
CONFIG=""
LIMIT=""
MAX_ACCURACY="0.30"
OUTPUT_ROOT="data"
SKIP_SNAPSHOT=0
ALLOW_UNASSESSED=0

usage() {
  cat <<'EOF'
Evaluate main-question hardness on a packed JSONL after dataset assessment passes.

Options:
  --local-dir PATH        Required packed JSONL
  --label NAME            Required unique metrics snapshot suffix
  --solver-provider NAME  azure|glm (default: azure)
  --config NAME           Dataset config label (default: packed filename stem)
  --limit N               Optional row cap (default: all rows)
  --max-accuracy F        Development hardness threshold (default: 0.30)
  --output-root DIR       Eval artifact root (default: data)
  --skip-snapshot         Do not copy metrics into data/packed/
  --allow-unassessed      Diagnostic run only: permit missing/failed quality report
  -h, --help              Show this help

Writes:
  data/processed/evals/<eval_id>/{metrics.json,predictions.jsonl}
  data/packed/luna_eval_metrics_<label>.json   (unless --skip-snapshot)

Exit codes:
  0  main_accuracy <= max-accuracy (development hardness gate passed)
  2  hardness gate failed
  other  runner/transport failure

Protocol: a sibling passing <pack>_quality_metrics.json is required by default.
--allow-unassessed results are non-gating and cannot support a quality claim.
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
    --allow-unassessed) ALLOW_UNASSESSED=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "${LABEL}" ]]; then
  echo "error: --label is required; use a unique experiment label" >&2
  usage >&2
  exit 2
fi
if [[ -z "${LOCAL_DIR}" ]]; then
  echo "error: --local-dir is required" >&2
  usage >&2
  exit 2
fi

if [[ ! -f "${LOCAL_DIR}" ]]; then
  echo "error: packed JSONL not found: ${LOCAL_DIR}" >&2
  exit 1
fi

METRICS_SNAPSHOT="${OUTPUT_ROOT}/packed/luna_eval_metrics_${LABEL}.json"
if [[ "${SKIP_SNAPSHOT}" -eq 0 && -e "${METRICS_SNAPSHOT}" ]]; then
  echo "error: metrics snapshot already exists: ${METRICS_SNAPSHOT}" >&2
  echo "Evaluation snapshots are immutable; choose a new --label." >&2
  exit 2
fi

PACK_STEM="$(basename "${LOCAL_DIR}" .jsonl)"
if [[ -z "${CONFIG}" ]]; then
  CONFIG="${PACK_STEM}"
fi
QUALITY_METRICS="$(dirname "${LOCAL_DIR}")/${PACK_STEM}_quality_metrics.json"
integrity_report="$(uv run python scripts/validate-packed-dataset.py "${LOCAL_DIR}")"
current_dataset_hash="$(
  printf '%s\n' "${integrity_report}" | uv run python -c \
    'import json,sys; print(json.load(sys.stdin)["dataset_sha256"])'
)"
if [[ ! -f "${QUALITY_METRICS}" ]]; then
  if [[ "${ALLOW_UNASSESSED}" -eq 0 ]]; then
    echo "error: required quality report missing: ${QUALITY_METRICS}" >&2
    echo "Run assess first, or use --allow-unassessed for a non-gating diagnostic." >&2
    exit 3
  fi
  echo "warning: unassessed diagnostic; result cannot support a quality claim" >&2
else
  read -r quality_passed assessed_dataset_hash < <(
    uv run python -c \
      'import json,sys; d=json.load(open(sys.argv[1])); print(str(bool(d["passed"])).lower(), d.get("dataset_sha256","missing"))' \
      "${QUALITY_METRICS}"
  )
  if [[ "${quality_passed}" != "true" ]]; then
    if [[ "${ALLOW_UNASSESSED}" -eq 0 ]]; then
      echo "error: dataset quality report failed: ${QUALITY_METRICS}" >&2
      echo "Hardness cannot compensate; use --allow-unassessed only for diagnostics." >&2
      exit 3
    fi
    echo "warning: failed-quality diagnostic; result cannot support a quality claim" >&2
  fi
  if [[ "${assessed_dataset_hash}" != "${current_dataset_hash}" ]]; then
    if [[ "${ALLOW_UNASSESSED}" -eq 0 ]]; then
      echo "error: quality report does not identify the current dataset" >&2
      echo "assessed=${assessed_dataset_hash} current=${current_dataset_hash}" >&2
      echo "Rerun assess; legacy reports without dataset_sha256 are non-gating." >&2
      exit 3
    fi
    echo "warning: quality report hash mismatch; result cannot support a quality claim" >&2
  fi
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
  printf '%s\n' "${report}" | uv run python -c \
    'import json,sys; print(json.load(sys.stdin).get("artifact_dir",""))' 2>/dev/null || true
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

echo "Complete the record in docs/engineering/assessments/dataset-quality-iterations.md"
exit "${eval_code}"
