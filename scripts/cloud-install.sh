#!/usr/bin/env bash
# Idempotent dependency sync for Cursor Cloud Agents (and local parity).
set -euo pipefail

export PATH="${HOME}/.local/bin:/usr/local/bin:${PATH}"

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

uv --version
uv python install 3.12
# --frozen: use committed uv.lock; --all-groups: include dev tools (pytest, ruff, …)
uv sync --frozen --all-groups

uv run python -c "import cogito_mill, langgraph, deepagents; print('cogito-mill imports ok', cogito_mill.__version__)"
