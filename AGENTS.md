# Agent notes — Cogito Mill

## What this repo is

Pipeline for generating long-form agentic reasoning datasets, orchestrated with LangGraph / Deep Agents, using custom Azure OpenAI deployments and GLM, publishing under [ksopyla on Hugging Face](https://huggingface.co/ksopyla/datasets).

## Environment

| Context | How |
|--------|-----|
| Local | `uv sync` then `uv run …` |
| Cloud | `.cursor/Dockerfile` + `scripts/cloud-install.sh` via `.cursor/environment.json` |

Secrets (local `.env` or Cursor Cloud Secrets): see `.env.example`.

## Cursor Cloud specific instructions

- Boot path: image from `.cursor/Dockerfile` → `bash scripts/cloud-install.sh` (`uv sync --frozen --all-groups`).
- Always use `uv run …` for Python tools; do not create a separate venv with `python -m venv`.
- After boot, verify with `uv run pytest tests/unit -q` before larger work.
- Secrets must come from Cursor Cloud Secrets (never invent keys). If Azure/GLM/HF vars are missing, work offline on code/docs/tests that do not call providers.
- Do not assume marketplace Hugging Face plugins; use project skill `huggingface-datasets` + `huggingface_hub`.
- Environment config is commit-scoped: push Dockerfile/`environment.json` changes before launching a cloud agent to test them.
- `uv run mypy` reports `Package 'cogito_mill' cannot be type checked due to missing py.typed marker` and exits 0 — this is a known packaging gap in the scaffold, not a lint/type failure.

## Subagents (project)

Defined under `.cursor/agents/`:

- `research-scout` — readonly background scout for papers, datasets, Hub cards, and repos (arXiv / OpenReview / ACL / HF / GitHub). Invoke with `/research-scout` or by asking for a literature / SoTA scan. Returns cited notes; does not decide mill design (use grilling / `/to-spec` for that). Substantial keepers → `docs/literature/`.

## Skills (project)

Installed under `.agents/skills/` (also discovered by Cursor):

- `/grill-me`, `/grilling`, `/grill-with-docs` — stress-test plans
- `/to-spec` — turn settled discussion into a spec
- `/tdd`, `/codebase-design`, `/domain-modeling` — engineering discipline
- `langgraph` — LangGraph patterns
- `/azure-usage` — Azure Foundry/OpenAI usage and costs via `az` (no secrets in skill)
- `huggingface-datasets` — Dataset Viewer / Hub upload (lightweight; not the marketplace HF plugin)
- `dataset-quality` — pilot pack assessment protocol, quality gates, iteration log, generate/evaluate launchers

## Specs

Living engineering docs: `docs/engineering/`. Refine with `/grill-with-docs` and `/to-spec`.

Dataset quality iterations: read `.agents/skills/dataset-quality/SKILL.md` before
changing generation or evaluation, then append measurements to
`docs/engineering/assessments/pilot-quality-iterations.md`. Launchers:
`scripts/generate-pilot.sh`, `scripts/evaluate-pilot.sh`.

## Tests

```bash
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/e2e
```

## Branching

- `main` — stable / release
- `dev` — shared synchronization point; land integration work here
- Feature branches — cut from `dev`, open PRs into `dev` (promote `dev` → `main` when ready)
