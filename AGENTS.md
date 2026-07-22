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
- `dataset-quality-judge` — readonly coordinator that prepares an evidence packet and calls `scripts/run-external-quality-judge.py` (Azure `gpt-5.6-terra-stories` by default). Use for independent quality assessment of retained packs; does not edit the mill or substitute its own judgment when Azure fails.

## Skills (project)

Installed under `.agents/skills/` (also discovered by Cursor):

- `/grill-me`, `/grilling`, `/grill-with-docs` — stress-test plans
- `/to-spec` — turn settled discussion into a spec
- `/tdd`, `/codebase-design`, `/domain-modeling` — engineering discipline
- `langgraph` — LangGraph patterns
- `/azure-usage` — Azure Foundry/OpenAI usage and costs via `az` (no secrets in skill)
- `huggingface-datasets` — Dataset Viewer / Hub upload (lightweight; not the marketplace HF plugin)
- `dataset-quality` — mandatory protocol for every dataset-quality change; metrics, controlled experiments, append-only records, and launchers

## Specs

Living engineering docs: `docs/engineering/`. Refine with `/grill-with-docs` and `/to-spec`.

### Mandatory dataset-quality preflight

For **every** change that can affect generated content, formal worlds, evidence, prompts,
handoffs, agent/graph logic, critics, quality thresholds, scoring, packing, evaluation, or a
quality claim, load and follow:

1. `.agents/skills/dataset-quality/SKILL.md`
2. `.agents/skills/dataset-quality/QUALITY-METRICS.md`
3. `.agents/skills/dataset-quality/ASSESSMENT-PROTOCOL.md`
4. `docs/engineering/assessments/dataset-quality-iterations.md`
5. latest relevant history in `docs/engineering/assessments/pilot-quality-iterations.md`
6. `data/packed/README.md`
7. both contracts under `schemas/`

Pre-register every measured improvement using
`.agents/skills/dataset-quality/ASSESSMENT-RECORD-TEMPLATE.md`, then append results to
`docs/engineering/assessments/dataset-quality-iterations.md`. Do not overwrite baselines or
modify Hub schemas during routine quality work. Canonical launchers:
`scripts/generate-dataset.sh`, `scripts/evaluate-dataset.sh`.

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
