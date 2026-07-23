#!/usr/bin/env bash
# Generate an isolated dataset candidate, pack it, and run assess gates.
# Usage:
#   scripts/generate-pilot.sh
#   scripts/generate-pilot.sh --n 12 --seeds-from 10000 --config pilot_v2 --agent-mode live
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

N=12
SEEDS_FROM=10000
CONFIG=""
PROVIDER="azure"
DIFFICULTY="very_hard"
AGENT_MODE="live"
OUTPUT_ROOT="data"
N_SUSPECTS=6
N_DISTRACTORS=6
MAX_ATTEMPTS=""
SKIP_ASSESS=0

usage() {
  cat <<'EOF'
Generate accepted dataset items, pack them to <output-root>/packed/<config>.jsonl, and assess.
The output root must not contain prior processed items; this prevents pack contamination.

Options:
  --n N                 Accepted items to generate (default: 12)
  --seeds-from N        Starting seed (default: 10000)
  --config NAME         Required unique candidate config / JSONL basename
  --provider NAME       azure|glm (default: azure)
  --difficulty NAME     medium|hard|very_hard (default: very_hard)
  --agent-mode MODE     offline|live (default: live)
  --output-root DIR     Artifact root (default: data)
  --n-suspects N        Recipe suspects (default: 6)
  --n-distractors N     Recipe distractors (default: 6)
  --max-attempts N      Optional generation attempt cap
  --skip-assess         Pack only; do not run assess
  -h, --help            Show this help

Writes:
  <output-root>/packed/<config>.jsonl
  <output-root>/packed/<config>_appendix.jsonl  (solver companion, if generated)
  <output-root>/packed/<config>_integrity_metrics.json
  <output-root>/packed/<config>_quality_metrics.json  (unless --skip-assess)

See .agents/skills/dataset-quality/SKILL.md for the assessment protocol.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --n) N="$2"; shift 2 ;;
    --seeds-from) SEEDS_FROM="$2"; shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --difficulty) DIFFICULTY="$2"; shift 2 ;;
    --agent-mode) AGENT_MODE="$2"; shift 2 ;;
    --output-root) OUTPUT_ROOT="$2"; shift 2 ;;
    --n-suspects) N_SUSPECTS="$2"; shift 2 ;;
    --n-distractors) N_DISTRACTORS="$2"; shift 2 ;;
    --max-attempts) MAX_ATTEMPTS="$2"; shift 2 ;;
    --skip-assess) SKIP_ASSESS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "${CONFIG}" ]]; then
  echo "error: --config is required; use a new non-baseline name for each experiment" >&2
  usage >&2
  exit 2
fi

PACKED_JSONL="${OUTPUT_ROOT}/packed/${CONFIG}.jsonl"
INTEGRITY_JSON="${OUTPUT_ROOT}/packed/${CONFIG}_integrity_metrics.json"
METRICS_JSON="${OUTPUT_ROOT}/packed/${CONFIG}_quality_metrics.json"

if compgen -G "${OUTPUT_ROOT}/processed/*/hub-item.json" >/dev/null; then
  echo "error: ${OUTPUT_ROOT}/processed already contains accepted items" >&2
  echo "Use a clean --output-root so this candidate cannot include unrelated runs." >&2
  exit 2
fi
if [[ -e "${PACKED_JSONL}" || -e "${INTEGRITY_JSON}" || -e "${METRICS_JSON}" ]]; then
  echo "error: candidate artifacts already exist; baselines and measured candidates are immutable" >&2
  echo "Choose a new --config or clean --output-root." >&2
  exit 2
fi

echo "==> generate-batch n=${N} seeds_from=${SEEDS_FROM} provider=${PROVIDER} agent_mode=${AGENT_MODE}"
gen_args=(
  generate-batch
  --n "${N}"
  --seeds-from "${SEEDS_FROM}"
  --provider "${PROVIDER}"
  --difficulty "${DIFFICULTY}"
  --agent-mode "${AGENT_MODE}"
  --output-root "${OUTPUT_ROOT}"
  --n-suspects "${N_SUSPECTS}"
  --n-distractors "${N_DISTRACTORS}"
)
if [[ -n "${MAX_ATTEMPTS}" ]]; then
  gen_args+=(--max-attempts "${MAX_ATTEMPTS}")
fi
uv run cogito-mill "${gen_args[@]}"

echo "==> publish dry-run -> ${PACKED_JSONL}"
uv run cogito-mill publish \
  --input "${OUTPUT_ROOT}/processed" \
  --dry-run \
  --config "${CONFIG}" \
  --output-root "${OUTPUT_ROOT}"

if [[ ! -f "${PACKED_JSONL}" ]]; then
  echo "error: expected packed file missing: ${PACKED_JSONL}" >&2
  exit 1
fi

echo "==> validate schema/integrity -> ${INTEGRITY_JSON}"
uv run python scripts/validate-packed-dataset.py \
  "${PACKED_JSONL}" \
  --output "${INTEGRITY_JSON}"

if [[ "${SKIP_ASSESS}" -eq 1 ]]; then
  echo "==> skip assess (${PACKED_JSONL} written)"
  exit 0
fi

echo "==> assess narration/diversity -> ${METRICS_JSON}"
set +e
uv run cogito-mill assess \
  --local-dir "${PACKED_JSONL}" \
  --output "${METRICS_JSON}"
assess_code=$?
set -e

if [[ "${assess_code}" -ne 0 ]]; then
  echo "assess FAILED (exit ${assess_code}). Fix narration/diversity before hardness eval." >&2
  echo "Metrics: ${METRICS_JSON}" >&2
  exit "${assess_code}"
fi

echo "assess PASSED"
echo "Pack:    ${PACKED_JSONL}"
echo "Integrity: ${INTEGRITY_JSON}"
echo "Metrics: ${METRICS_JSON}"
echo "Next:    scripts/evaluate-dataset.sh --local-dir ${PACKED_JSONL} --config ${CONFIG} --label <experiment>"
