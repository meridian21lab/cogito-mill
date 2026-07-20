# Architecture (draft)

## Package map

```text
src/cogito_mill/
  config/       # Settings (Azure, GLM, HF)
  llm/          # Provider factories
  agents/       # Deep Agents + LangGraph graphs
  pipelines/    # Stage orchestration (design → publish)
  datasets/     # Schema, pack, Hub I/O
  validation/   # Answerability / consistency / schema checks
  cli.py        # Entry points
```

## Runtime stack

```text
Deep Agents (harness: planning, filesystem, subagents)
        │
        ▼
LangGraph (durable graph runtime)
        │
        ▼
LangChain chat models ── Azure OpenAI deployments
                      └─ GLM (OpenAI-compatible base URL)
```

## Suggested agent roles (to grill)

| Role | Responsibility |
|------|----------------|
| Designer | Premise, cast, clue map, constraints |
| Writer | Long-form story consistent with clue map |
| Solver adversary | Attempt solution without gold key; flag leaks |
| Verifier | Schema + grounding checks |
| Publisher | Pack + push to `ksopyla/<dataset>` |

Exact graph topology (single deep agent vs supervisor of specialists) is an open decision — see `04-open-questions.md`.

## Tests

| Layer | Lives in | Intent |
|-------|----------|--------|
| Unit | `tests/unit/` | Pure functions, schemas, validators |
| Integration | `tests/integration/` | Provider wiring, Hub client (marked; may need secrets) |
| E2E | `tests/e2e/` | Full mill stage on fixtures (expensive / gated) |
