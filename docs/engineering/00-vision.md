# Vision — Cogito Mill

## Goal

Build a reproducible mill that generates **long narrative puzzles requiring multi-hop deduction**, with gold reasoning traces suitable for training and evaluating agentic reasoners.

Datasets are shared on Hugging Face under [`ksopyla`](https://huggingface.co/ksopyla/datasets).

## In scope

- Orchestration with **LangGraph** and **Deep Agents** (`deepagents`)
- Multi-provider LLMs: **custom Azure OpenAI deployments** and **GLM** (OpenAI-compatible)
- Local + Cursor Cloud workflows via **uv**
- Validation gates before publish
- Dataset packaging and Hub upload

## Out of scope (for now)

- Training models in this repo
- Serving inference APIs
- The large Hugging Face Cursor marketplace plugin (we use the slim `huggingface-datasets` skill + `huggingface_hub`)

## Success signals

- Specs in this folder are grilled and ticketed before large implementation
- Agents can generate → validate → publish with secrets from env / Cloud Secrets
- Unit / integration / e2e tests cover the mill stages we actually ship
