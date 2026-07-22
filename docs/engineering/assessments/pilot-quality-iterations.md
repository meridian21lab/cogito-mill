# Pilot quality assessment log

Living log of blunt assessments against packed pilots. Newest iteration at the bottom.

**Protocol (single reference):** `.agents/skills/dataset-quality/SKILL.md`.
Use `ITERATION-TEMPLATE.md` in that skill when appending. Launchers:
`scripts/generate-pilot.sh`, `scripts/evaluate-pilot.sh`.

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

## Iteration 1 — pilot_v1 (2026-07-21)

Source: regenerated `data/packed/pilot_v1.jsonl` (150) + Luna sample eval (`luna_eval_metrics_v1.json`).

### What changed

1. **Narration** — Multi-paragraph mysteries with cast, scenes, and connective tissue. EMP budget ~9–14 load-bearing codes; ≤1 personnel-index line (no 48-line dumps).
2. **Questions** — Always 4 scored QAs: main, lender intermediate, counterfactual (`none`), badge-code probe. Name questions demand **full name (given + surname)**.
3. **Variants** — 1–3 `gold_answer_variants` (e.g. `Morgan Okada` / `Okada, Morgan`); eval uses `score_exact_any`.
4. **Critic** — Deterministic blind story critic in LangGraph (`critique_story` node) + versioned prompts under `agents/prompts/`.
5. **Anti-shortcut** — Shared given names, no contiguous gold full name in prose, locker-mediated surname hop + twin-name red herring.

### Luna sample (12 stories / 48 QAs)

- Overall accuracy: **0.94**
- Main accuracy: **1.00** (hardness gate ≤0.30 **failed**)
- First-name-only rate: **0.00** (was 0.38 on v0)

### Honest verdict

- **Readable + answer-form fix: success.** Humans can follow the plot; exact-match no longer loses on first-name-only when the model solves it.
- **Hardness gate: not met.** Clean template logic is now easy for Azure writer/Luna. v0 “hardness” was mostly illegibility, which we correctly removed per product vision.
- **Agent graph: still template-backed.** Critic + prompts land; full concept/formalizer/scene-writer LLM roles remain future work per `01-architecture.md`.

### Next improvement targets

1. Deeper worlds (more events, branching distractor graphs) so unique entailment stays hard without EMP walls.
2. Optional LLM scene writer behind the same critic gates.
3. Keep main-accuracy as the hardness metric; do not reintroduce identifier dumps.
4. Consider separate “readable pilot” vs “hard benchmark” configs once worlds are rich enough.

---

## Iteration 2 — explicit agents + concept portfolio (2026-07-21)

Hypothesis: replacing the single access-timeline template with explicit planner,
concept-critic, formalizer/verifier, storyteller, story-critic, and final-critic roles would
fix repetition and make structural difficulty controllable.

### What changed

1. The LangGraph became an explicit conditional graph with bounded concept and story repairs.
2. Writer and judge deployments are injected behind narrow role interfaces; offline tests use
   deterministic adapters.
3. Six narrative families replaced the one access-timeline skin: watch handover, archive
   provenance, fault network, delegated authority, expedition signal, and workshop provenance.
4. Dataset-level narration, duplicate, setting, template-share, opening, question-stem, and
   5-shingle similarity gates were added.

### Measured result

- Live dev pack: 12 stories, all narration/diversity gates passed.
- Six families were balanced at two stories each; exact duplicates: 0; unique openings: 100%.
- Pairwise story 5-shingle similarity: P95 **0.164**, max **0.250**.
- Luna main accuracy: **12/12 (100%)** — failed.

### Verdict

Architecture and diversity improved, but the final concept was still a shallow intersection
of visibly matching branches. More agents did not itself create harder reasoning.

---

## Iteration 3 — transformation chains and linear checksum (2026-07-21)

Hypothesis: raw clue → channel → status transformations plus a weighted checksum would remove
the direct-intersection shortcut.

### Measured result

- The blind story critic rejected early versions that serialized conversion tables; unused
  mappings were removed and shared inference rules were narrated once.
- Luna still solved the transformation probes and scored **8/8 (100%)** on the balanced
  random linear-checksum sample.

### Verdict

Linear arithmetic remained easy for Luna. Difficulty could not come from adding lookup layers;
those layers also pushed narration back toward disguised tables.

---

## Iteration 4 — nonlinear one-pass checksum (2026-07-21)

Hypothesis: a seed-specific recurrence
`state = (state² + coefficient × status_value) mod prime` over the six independently grounded
evidence streams would test execution of a newly defined local concept.

### Measured result

- Narration/diversity gate: passed on 12/12 live-agent stories.
- Word range: 730–953; six template families; P95 story similarity below 0.10.
- Luna main accuracy: **9/12 (75%)** — improved, but failed.

---

## Iteration 5 — three-pass nonlinear checksum (2026-07-21)

Hypothesis: forward, reverse, then coefficient-rotated passes would raise state-tracking depth
without adding prose or identifiers.

### Measured result

- Narration passed on all 7 accepted calibration items.
- Luna main accuracy: **5/7 (71.4%)** — failed.
- A model critic incorrectly recomputed one checksum. Deterministic regression tests now lock
  the recurrence; the final prose critic is explicitly advisory on arithmetic.

---

## Iteration 6 — variable 17–29-cycle checksum (2026-07-21)

Hypothesis: varying recurrence depth by seed would prevent a fixed short-computation shortcut.

### Measured result

- A fresh six-item sample scored **0/6 (0%)**, but the balanced 12-item pack scored
  **5/12 (41.7%)** — failed the ≤30% gate.
- All 12 narration/diversity gates passed: 736–1034 words, six families represented,
  100% unique openings/stems, P95 5-shingle similarity **0.096**, no duplicates.

### Next refinement

Increase the seed-dependent cycle range without adding any narrative records. Re-evaluate the
same quality gates first, then Luna on all 12 main questions.

---

## Iteration 7 — pilot_v2, variable 97–127-cycle concept (2026-07-21)

Source: `data/packed/pilot_v2.jsonl` (12 live-agent calibration items),
`pilot_v2_quality_metrics.json`, and `luna_eval_metrics_v2.json`.

### What changed

1. The same six grounded evidence statuses feed the nonlinear recurrence; no clues, codes, or
   filler were added.
2. The seed-specific cycle count increased to 97–127 complete forward/reverse/rotated cycles.
3. The exact cycle count and operation depth are retained per item.
4. A regression test executes the disclosed recurrence. LLM critics judge narration and
   usability but cannot overrule deterministic arithmetic.

### Narration and diversity (12/12 gate passed)

- Narration: **12/12**; 745–1277 words (median 902).
- Exact duplicate stories: **0**.
- Structural families represented: **6**; effective family count **5.14**; max share **0.25**.
- Unique openings: **100%**.
- Unique main-question stems: **100%**.
- Pairwise token 5-shingle similarity: P95 **0.087**, max **0.097**.
- Settings represented: 5; normalized setting entropy **0.943**.
- Every item passed deterministic grounding plus model story/final critics.

### Luna main-question evaluation

- Correct: **2/12**.
- Main accuracy: **16.7%** — development hardness gate **passed** (target <30%).
- Transport failures: **0**.
- First-name-only errors: **0/12**.
- One-sided 95% Wilson upper bound: **39.9%** — statistical release gate not yet met.

### Honest verdict

- Requested development quality gates are met simultaneously: readable narration, low surface
  overlap across six families, and Luna below 30%.
- This is a calibration pack, not a release-sized benchmark. The hardness mechanism primarily
  tests execution of a newly defined iterative concept over grounded evidence. The next scale
  iteration should add other hard structural mechanisms (state transitions, provenance DAGs,
  and constraint worlds) so difficulty diversity catches up with narrative diversity.
- A larger balanced pack is required before claiming the ≤30% bound statistically.

---
