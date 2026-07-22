# Cogito Mill — Claude Code guide

> **Interchangeable with Cursor.** `AGENTS.md` is the single source of truth for
> shared agent instructions and is read by both Claude Code and Cursor. This file
> imports it and adds only Claude-Code-specifics on top. When you add context
> that *both* tools need, put it in `AGENTS.md` — not here.

@AGENTS.md

## Claude ↔ Cursor parity

| Concern | Cursor | Claude Code |
|--------|--------|-------------|
| Project memory | `.cursor/rules/project.mdc` (alwaysApply) + `AGENTS.md` | this file (`@AGENTS.md`) |
| Subagents | `.cursor/agents/` | `.claude/agents/` |
| Skills | `.agents/skills/` (shared source) | `.claude/skills/` → symlinked to `.agents/skills/` |
| Cloud env | `.cursor/Dockerfile` + `.cursor/environment.json` | run locally with `uv` (no Claude cloud image) |
| HF / Azure | `.cursor/settings.json` plugins | `hf` CLI + `huggingface_hub`; Azure via env vars |

## Skills (shared — same slash commands in both tools)

Project skills live in `.agents/skills/` and are surfaced to Claude through
`.claude/skills/` symlinks, so the identical commands work here:

- `/grill-me`, `/grilling`, `/grill-with-docs` — stress-test plans and specs
- `/to-spec` — turn settled discussion into a spec
- `/tdd`, `/codebase-design`, `/domain-modeling` — engineering discipline
- `/langgraph` — LangGraph patterns for the mill pipeline
- `/azure-usage` — Azure Foundry/OpenAI usage and costs via `az` (no secrets in skill)
- `/dataset-quality` — mandatory protocol and metric registry for every dataset-quality change

> `huggingface-datasets` is listed in `skills-lock.json` but **not present on
> disk**. For Hub work, use the `hf` CLI and `huggingface_hub` directly (auth via
> `HF_TOKEN`). Prefer the existing `/grill-with-docs` → `/to-spec` flow over
> inventing one-off skills.

## Subagents

- **`research-scout`** — readonly scout for papers, datasets, Hub cards, and
 repos (arXiv / OpenReview / ACL / PMLR / HF / GitHub). Spawn it (Agent tool)
 for a literature / SoTA scan; it returns cited notes and does **not** decide
 mill design — use `/grilling` or `/to-spec` for that. Substantial keepers →
 `docs/literature/`.
- **`dataset-quality-judge`** — readonly assessment coordinator. Prepares an
 evidence packet and invokes `scripts/run-external-quality-judge.py` (Azure
 `gpt-5.6-terra-stories`). Does not judge quality itself or edit artifacts.

## Running things

```bash
uv sync                       # install / sync deps
uv run pytest tests/unit -q   # fast, offline, deterministic — run before larger work
uv run ruff check src tests
uv run mypy
uv run cogito-mill …          # pilot CLI: generate-batch | publish | evaluate
```

Local CLIs on the Mac (`hf`, `gh`, `az`) are installed system-wide; prefer
env / secrets over interactive login inside agents.

## Editing shared config

- **Shared** context (both tools) → `AGENTS.md`.
- **Claude-only** behavior → this file or `.claude/`.
- **Cursor-only** behavior → `.cursor/`.
- Keep `.claude/skills/` as symlinks into `.agents/skills/` — never copy, or the
  two tools will drift when skills update via `skills-lock.json`.
