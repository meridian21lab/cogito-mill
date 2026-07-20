# Open questions

Use `/grill-me` or `/grill-with-docs` on these before locking implementation.

1. **Story length & format** — target tokens/words; freeform vs MCQ vs both?
2. **Genre scope** — mystery only, or also formal logic / sci-fi / legal?
3. **Graph shape** — one Deep Agent with skills vs LangGraph supervisor of specialists?
4. **Provider split** — which stages run on Azure deployments vs GLM?
5. **Gold reasoning format** — step list with character spans? tool traces?
6. **Difficulty labeling** — human rubric, model-judge, or structural (hop count)?
7. **Eval harness** — held-out solvers; which models; pass@k?
8. **Licensing** — dataset license for Hub release?
9. **Batch orchestration** — Cursor Cloud Agents / SDK vs local mill only?
10. **Idempotency** — how do we version and resume partial generations?

Capture decisions as ADRs via `/grill-with-docs` → `docs/domain/`.
