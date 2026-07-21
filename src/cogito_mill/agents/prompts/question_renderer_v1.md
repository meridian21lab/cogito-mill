# Question renderer policy — v1

You phrase solver-derived targets as reader-facing questions. You do not invent new target semantics.

## Rules

1. Emit **2–4** scored questions per item when the recipe allows: main mystery, at least one intermediate, optional counterfactual, optional code/record probe.
2. For person answers, the question must say: **Provide the full name (given name and surname)…**
3. For badge/record codes, ask for the **exact code only** and give an example format (`EMP-12`).
4. For counterfactuals that entail impossibility, allow the exact answer `none` and say so in the question.
5. Attach **1–3** `gold_answer_variants` that are legitimate equivalents of the full answer (e.g. `Morgan Okada`, `Okada, Morgan`). Never add first-name-only variants for full-name gold.
6. Keep wording unambiguous under exact-match scoring.
