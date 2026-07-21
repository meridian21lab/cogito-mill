# Pilot quality assessment log

Living log of blunt assessments against packed pilots. Newest iteration at the bottom.

---

## Iteration 0 — pilot_v0 (2026-07-21)

Source: `data/packed/pilot_v0.jsonl` (150 items) + `luna_eval_metrics.json`.

### What is broken (story)

1. **Not a story.** After a one-line setting open, the text dumps ~48 `Personnel index: EMP-NN resolves to Name` lines. That is a lookup table, not narration.
2. **Unreadable for humans.** ~58 badge-code tokens per item; median ~850 words, most of them noise. A reader cannot track plot because there is almost none.
3. **Clues are bolted on, not dramatized.** Required facts are concatenated as flat sentences inside three “scenes” that are just bags of obligations.
4. **Padding is filler.** Coffee machines, lunch arguments, radio chatter add length without supporting deduction or atmosphere that serves the mystery.
5. **Surface is identical across the batch.** Six question stems × six settings; same timeline skeleton (09:00 loan → 09:25 hold → 10:10 discovery). Diversity is cosmetic.

### What is broken (questions / answers)

1. **Only one scored question** per item (`Who {action}?`), despite the domain contract calling for a bundle (main + intermediates + counterfactual + falsifier).
2. **Answer form is underspecified.** Gold is a full name (`Morgan Okada`); the question does not say “full name”. Luna eval: **0% exact**, **38% first-name-only** — models often get the right person and lose on string match.
3. **No answer variants.** Exact match has no room for legitimate equivalents (`Okada, Morgan`).

### What is broken (agents / graph)

1. **Agents package is a stub.** `src/cogito_mill/agents/` has no planners, critics, or prompts. Spec in `01-architecture.md` is unimplemented.
2. **Graph is three nodes:** `sample_recipe → formalize_and_disclose → final_validate`. No concept loop, no blind story critic, no question renderer role, no repair edges.
3. **Template is the generator.** `build_access_timeline` invents world + prose + questions in one function. Deterministic solver gates uniqueness, but **nothing gates readability or narrative coherence**.
4. **Hardness was bought with illegibility** (decoy EMP walls, buried name maps), not with cleaner multi-hop structure. That fights the vision: natural prose, latent logic, unique entailment.

### What still works

- Formal world + Z3/causal uniqueness gate is the right spine.
- Shared-surname anti-heuristic and code→name hops are good reasoning ideas — badly rendered.
- Offline generate/pack/eval CLI path is usable.

### Improvement targets (for next iterations)

1. Coherent multi-paragraph narration; identifiers only where they create real hops.
2. Story critic with explicit readability + grounding rubric; reject/repair on fail.
3. 2–4 precise questions per item; demand full-name (or exact code) form.
4. 1–3 gold answer variants; score any match.
5. Prompts + graph roles aligned with architecture; keep “agents propose, code decides”.

### Success criteria (quality bar)

- Human can read a generated story as a short mystery without wading through ID dumps.
- Badge/personnel codes appear sparsely and are load-bearing for at least one hop.
- Each item has 2–4 questions with explicit answer-form instructions.
- Exact-match scoring accepts listed variants; questions ask for full names where names are gold.
- Deterministic critic rejects EMP-wall / non-narrative dumps.
- Luna eval still useful as hardness signal, but **readability is not traded for hardness**.

---
