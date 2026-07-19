# Agent notes — Cogito Mill

## What this repo is

Pipeline for generating long-form agentic reasoning datasets, orchestrated with LangGraph / Deep Agents, using custom Azure OpenAI deployments and GLM, publishing under [ksopyla on Hugging Face](https://huggingface.co/ksopyla/datasets).

## Environment

| Context | How |
|--------|-----|
| Local | `uv sync` then `uv run …` |
| Cloud | `.cursor/environment.json` runs uv install + `uv sync --frozen --all-extras` |

Secrets (local `.env` or Cursor Cloud Secrets): see `.env.example`.

## Skills (project)

Installed under `.agents/skills/` (also discovered by Cursor):

- `/grill-me`, `/grilling`, `/grill-with-docs` — stress-test plans
- `/to-spec` — turn settled discussion into a spec
- `/tdd`, `/codebase-design`, `/domain-modeling` — engineering discipline
- `langgraph` — LangGraph patterns
- `huggingface-datasets` — Dataset Viewer / Hub upload (lightweight; not the marketplace HF plugin)

## Specs

Living engineering docs: `docs/engineering/`. Refine with `/grill-with-docs` and `/to-spec`.

## Tests

```bash
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/e2e
```
