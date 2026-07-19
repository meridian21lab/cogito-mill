# Cogito Mill

Agentic reasoning **dataset generation** mill: long multi-hop deduction stories, orchestrated with LangGraph / Deep Agents, using custom Azure OpenAI deployments and GLM, published to [Hugging Face `@ksopyla`](https://huggingface.co/ksopyla/datasets).

## Quick start (local)

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
cp .env.example .env   # fill Azure / GLM / HF secrets
uv run pytest tests/unit
uv run cogito-mill
```

## Cursor Cloud

`.cursor/environment.json` installs uv (if needed) and runs `uv sync --frozen --all-extras`. Add the same secrets as `.env.example` in the Cloud Agents Secrets UI.

See `AGENTS.md` for agent conventions and installed skills.

## Layout

| Path | Role |
|------|------|
| `src/cogito_mill/` | Application package |
| `tests/{unit,integration,e2e}/` | Test pyramid |
| `docs/engineering/` | Specs we refine together |
| `.agents/skills/` | Installed engineering skills |
| `.cursor/rules/` | Always-on project rules |

## Skills

Matt Pocock: `grill-me`, `grilling`, `grill-with-docs`, `to-spec`, `tdd`, `codebase-design`, `domain-modeling`  
LangGraph: `langgraph`  
Hugging Face (slim): `huggingface-datasets` — not the marketplace HF plugin
