#!/usr/bin/env bash
# Idempotent dependency sync for Cursor Cloud Agents (and local parity).
set -euo pipefail

export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

uv --version
uv python install 3.12
# --frozen: use committed uv.lock; --all-groups: include dev tools (pytest, ruff, …)
uv sync --frozen --all-groups

uv run python -c "import cogito_mill, langgraph, deepagents; print('cogito-mill imports ok', cogito_mill.__version__)"

# Cursor Cloud launches custom agents by reading personal skills at
# ~/.cursor/skills/<name>/SKILL.md, not project agents at .cursor/agents/<name>.md
# or project skills at .agents/skills/. Mirror project agents there so cloud
# entrypoints (e.g. dataset-quality-judge) resolve.
agents_dir="${REPO_ROOT}/.cursor/agents"
skills_home="${HOME}/.cursor/skills"
if [[ -d "${agents_dir}" ]]; then
  mkdir -p "${skills_home}"
  for agent in "${agents_dir}"/*.md; do
    [[ -f "${agent}" ]] || continue
    name="$(basename "${agent}" .md)"
    dest="${skills_home}/${name}"
    mkdir -p "${dest}"
    cp "${agent}" "${dest}/SKILL.md"
    echo "mirrored agent ${name} -> ${dest}/SKILL.md"
  done
fi
