---
name: dataset-quality
description: Develop and assess Cogito Mill reasoning datasets. MUST be used for every change that can affect generated content, agents/prompts/handoffs, formal logic, grounding, quality gates, scoring, packed composition, evaluation, or dataset-quality claims.
---

# Dataset quality — Long Story Short

Entry point for **all dataset quality improvements**, from a one-prompt repair through a
release-sized dataset. This skill is not limited to pilot packs. Pilot artifacts are the current
baseline and historical evidence, not the boundary of the protocol.

## Required reading — load on every quality task

Read these files before planning or editing:

1. this file;
2. [QUALITY-METRICS.md](QUALITY-METRICS.md);
3. [ASSESSMENT-PROTOCOL.md](ASSESSMENT-PROTOCOL.md);
4. `docs/engineering/assessments/dataset-quality-iterations.md`;
5. the latest relevant entries in
   `docs/engineering/assessments/pilot-quality-iterations.md`;
6. `data/packed/README.md`;
7. both files under `schemas/`.

Then inspect the affected implementation because executable gates outrank prose. Follow
`ASSESSMENT-PROTOCOL.md`; use
[ASSESSMENT-RECORD-TEMPLATE.md](ASSESSMENT-RECORD-TEMPLATE.md) for every measured change.

Companion materials:

| Path | Role |
|------|------|
| `QUALITY-METRICS.md` | Canonical formulas, gates, diagnostics, and claim levels |
| `ASSESSMENT-PROTOCOL.md` | Detailed reproducible experiment procedure |
| `ASSESSMENT-RECORD-TEMPLATE.md` | Pre-registration and result record |
| `data/packed/README.md` | Immutable retained packs and metric snapshots |
| `data/packed/` | Frozen packs, quality metrics, solver metrics |
| `docs/engineering/assessments/dataset-quality-iterations.md` | Active append-only log for all improvements |
| `docs/engineering/assessments/pilot-quality-iterations.md` | Historical pilot experiments |
| `schemas/reasoning-item.schema.json` | Hub thin item schema (**do not modify**) |
| `schemas/reasoning-item-full.schema.json` | Full accepted projection (**do not modify**) |
| `scripts/generate-dataset.sh` | Launch isolated batch generation + pack + assess |
| `scripts/evaluate-dataset.sh` | Launch solver hardness evaluation |

---

## Non-negotiables

1. **Keep the Hub schema.** Do not change fields, enums, or required keys in `schemas/` during
   quality iterations. Pack and eval remain compatible with the current contract.
2. **Agents propose; code decides.** Models write premises, prose, and critiques. Z3/causal uniqueness, deterministic story gates, and pack assessors decide acceptance.
3. **Readability is not traded for hardness.** Identifier dumps and EMP walls are failures even if Luna accuracy falls.
4. **Minor agent changes only.** Prefer prompt, handoff, and internal-logic improvements over new graph topology or role proliferation.
5. **Hardness cannot compensate for failed narration or diversity.** Run `assess` before Luna; if assess fails, stop and fix the pack.
6. **No unregistered quality claims.** Pre-register the hypothesis and controls, retain immutable
   artifacts/hashes, report failures, and append the completed experiment record.
7. **Do not overwrite baselines.** Every measured candidate gets a new config/label and output.

---

## Current implementation baseline (not protocol scope)

| Artifact | Meaning |
|----------|---------|
| `data/packed/pilot_v2.jsonl` | Prior 12-item live-agent calibration pack (six families, nonlinear local concept) |
| `data/packed/pilot_v2_quality_metrics.json` | Pack narration + diversity gates (passed) |
| `data/packed/luna_eval_metrics_v2.json` | Luna main-question hardness (16.7% = passed development gate) |
| `data/packed/pilot_v3_balanced.jsonl` | Prior 12-item calibration (evidence-edit CFs + appendix; hardness pass) |
| `data/packed/pilot_v3_balanced_appendix.jsonl` | Companion solver appendix for `pilot_v3_balanced` |
| `data/packed/luna_eval_metrics_v3_balanced_story.json` | Story-only Luna main accuracy 16.7% (hardness pass) |
| `data/packed/luna_eval_metrics_v3_balanced_appendix.json` | Appendix-assisted Luna main accuracy 100% |
| `data/packed/pilot_v4b_neutral.jsonl` | Anti-ledger timeline narration baseline (n=20; hardness fail at 100%) |
| `data/packed/luna_eval_metrics_v4b_neutral_story.json` | Story-only main accuracy 100% (too easy; not a hardness claim) |

Historical packs (`pilot_v0`, `pilot_v1`) and their Luna metrics remain for regression narrative
only. Iterate **forward** from `pilot_v2` lessons, but use the general experiment log and protocol
for every new change.

---

## Schema (frozen)

### Hub thin item (`schemas/reasoning-item.schema.json`)

Each JSONL row:

| Field | Contract |
|-------|----------|
| `id` | Stable item id |
| `story` | Self-contained narrative with dispersed evidence |
| `question` | Main mystery (also first/main of `questions`) |
| `gold_answer` | Canonical exact-match answer |
| `gold_answer_variants` | 1–3 accepted exact-match forms |
| `questions` | 2–4 scored QAs (`id`, `question`, `gold_answer`, `gold_answer_variants`, `question_type`) |
| `n_hops` | Structural hop count (≥10 for pack gate) |
| `setting_family` | `detective` \| `domestic` \| `workplace` \| `expedition` \| `historical` \| `speculative` |
| `difficulty_bucket` | `medium` \| `hard` \| `very_hard` |
| `template_id` | Narrative family id (or null) |

`question_type` enum: `main`, `intermediate`, `counterfactual`, `code`, `scalar`.

### Full accepted item (`schemas/reasoning-item-full.schema.json`)

Internal/processed projection with sentences, gold steps, counterfactual, falsifier, provenance. Not the default Hub Viewer schema. Packing projects full accepted items → thin `PilotHubItem` via `AcceptedItem.to_hub_item()`.

**When developing further:** extend generators, critics, and templates so they still emit valid thin rows. If a new field seems necessary, treat it as a future ADR + schema revision — out of scope for normal quality iterations.

---

## Agents and responsibilities

Prefer **prompt, handoff, and logic polish** inside existing roles. Do not add new graph stages unless an ADR requires it.

### Live graph (implemented)

```text
sample_recipe → plan_concept → critique_concept ──revise──► plan_concept
                                    │ accept
                                    ▼
                               formalize → verify ──fail──► reject_run
                                    │ ok
                                    ▼
                               tell_story → assemble_and_ground → critique_story
                                    ▲                              │ revise
                                    └──────── repair ──────────────┤
                                                                   │ accept
                                                                   ▼
                                                           critique_final
                                                                   │ revise → tell_story
                                                                   │ accept
                                                                   ▼
                                                           final_validate → accepted
```

| Role / node | Model | Responsibility | May decide |
|-------------|-------|----------------|------------|
| `sample_recipe` | code | Seed recipe, setting, difficulty, hop target | Recipe constraints only |
| Concept planner (`plan_concept`) | writer | Compact premise for a fixed family + local concept | Creative premise only |
| Concept critic (`critique_concept`) | judge | Formalizability, self-containment, no answer hint | Accept / revise / reject concept |
| Formalizer (`formalize`) | **code** (`build_concept_puzzle`) | Complete world, visible theory, QA bundle, story scaffold | Formal truth via templates |
| Verifier (`verify`) | **code** (`WorldSolver`) | World satisfiability + visible uniqueness | Accept / reject logic |
| Storyteller (`tell_story`) | writer | Realize obligations as coherent narration | Surface realization only |
| Assembler / grounding | **code** | Sentence map + required-fact grounding | Grounding pass/fail |
| Story critic (deterministic) | **code** | Readability + QA contract | Hard reject on fail |
| Story critic (model) | judge | Coherence, integration, no table-dump prose | Recommend revise/reject |
| Final critic | judge | Usability, self-containment, no answer leak | Recommend accept/revise/reject; **must not override arithmetic** |
| Final validate | **code** | Promote accepted item + hub projection | Terminal accept/reject |

Offline mode (`agent_mode=offline`) uses deterministic adapters that defer to code gates — required for unit/integration tests without secrets.

### Safe improvement surfaces

| Surface | Where | Examples |
|---------|-------|----------|
| Prompts | `src/cogito_mill/agents/prompts/`, inline prompts in `agents/roles.py` | Stronger anti-table instructions, clearer local-rule wording |
| Handoffs | Feedback strings into `plan` / `tell_story`; critic findings | More actionable revise text; preserve obligation IDs |
| Internal logic | `pipelines/concept_templates.py`, `agents/critics.py`, `validation/grounding.py` | Harder structural mechanisms, tighter readability checks |
| Pack gates | `eval/quality.py` | Thresholds only when calibration pack size changes intentionally |

### Out of scope for routine iterations

- New agent roles or Deep Agent supervisors
- Schema field additions on Hub items
- Trading narration for hardness (EMP walls, personnel-index dumps)
- Letting LLM critics overrule deterministic checksum / uniqueness

---

## Quality gates

Two layers: **per-story** (generation acceptance) and **pack-level** (dataset release readiness). Hardness is a third layer that runs only after pack gates pass.

### Per-story gates (each accepted item)

Implemented primarily in `agents/critics.py`, `validation/grounding.py`, and `pipelines/nodes.py`.

#### Deterministic story critic (`critique_story_document`)

| Gate id | Pass condition |
|---------|----------------|
| `narrative_paragraphs` | ≥4 non-empty paragraphs (pack assess uses ≥5) |
| `identifier_budget` | EMP tokens ≤14 (pack assess uses ≤6) |
| `no_personnel_dump` | `Personnel index:` lines ≤2 (pack assess uses ≤1) |
| `no_id_resolution_wall` | Code→name “resolves to” clauses ≤3 |
| `question_count` | 2–4 scored questions |
| `answer_form_clarity` | Name questions include “full name” |
| `answer_variants` | Each question has 1–3 `gold_answer_variants` |
| `human_readable_opening` | Opening is narration, not an ID table |
| `no_direct_token_transfer_reset` | Provenance transfers do not directly reveal the tracked token's new container |

#### Grounding (`critique_grounding`)

| Gate id | Pass condition |
|---------|----------------|
| `required_fact_grounding` | Every required visible fact sentence-anchored |
| `single_fact_realization` | Each required fact in exactly one scene |
| `known_scene_obligations` | No unknown obligation IDs |

#### Solver / final code gates

| Gate | Pass condition |
|------|----------------|
| World satisfiable | `WorldAnalysis.satisfiable` |
| Unique disclosure | Exactly one entailed answer on visible theory |
| Story critic accept | Combined deterministic + grounding + model story reports accept |
| Final critic accept | Model final critic accepts (arithmetic is advisory only) |

A story that fails any hard gate is **rejected** (or revised within repair budget), never packed.

### Pack-level gates (`cogito_mill.eval.quality.assess_dataset`)

Run on packed JSONL. Thresholds depend on pack size `n`:

| Gate id | `n < 100` (calibration) | `n ≥ 100` (release-sized) |
|---------|-------------------------|---------------------------|
| `narration` | 100% stories pass per-story narration metrics | ≥95% pass |
| `no_exact_duplicates` | 0 exact story hashes | same |
| `template_count` | ≥4 families | ≥6 |
| `template_effective_count` | ≥3.5 | ≥5.0 |
| `template_max_share` | ≤0.34 | ≤0.20 |
| `setting_coverage` | ≥4 settings | ≥6 |
| `setting_entropy` | ≥0.75 | ≥0.85 |
| `surface_similarity_p95` | 5-shingle Jaccard P95 ≤0.65 | same |
| `unique_openings` | ≥80% unique 24-token openings | same |
| `question_stems` | ≥ min(8, n) unique main stems | same |
| `question_stem_max_share` | ≤0.20 | same |
| `structural_hops` | every `n_hops` ≥10 | same |

Per-story **narration metrics** inside assess (stricter identifier budget than generation critic):

- ≥5 paragraphs
- 500–2500 words
- sentence length P95 ≤45 words
- `Personnel index:` ≤1
- `EMP-*` tokens ≤6
- direct tracked-token transfer resets: 0 for calibration packs (≤5% at release size)

`assess` exit code: `0` if `passed`, else `3`.

### Hardness gates (Luna / solver model, main question only)

Run with `cogito-mill evaluate --main-only` after assess passes.

| Gate | Metric | Pass |
|------|--------|------|
| Development hardness | `main_accuracy` | ≤0.30 |
| Statistical release hardness | one-sided 95% Wilson upper bound on main accuracy | ≤0.30 |
| Answer-form health | `first_name_only_rate` | ~0 (regression if rises) |
| Transport health | `transport_errors` | 0 |

Scoring: `score_exact_any` against `gold_answer_variants` (scorer version `pilot.v2`). Hardness metric is **main-question** accuracy, not all QAs.

Calibration packs (e.g. n=12) may pass development hardness while failing statistical release — record both honestly.

---

## Where to record assessments and metrics

| What | Where |
|------|-------|
| Packed items | `data/packed/<config>.jsonl` (immutable once measured) |
| Schema/ID/hash integrity | `data/packed/<config>_integrity_metrics.json` |
| Pack quality metrics | `data/packed/<config>_quality_metrics.json` |
| Solver metrics (current filename convention) | `data/packed/luna_eval_metrics_<label>.json` |
| Solver prediction samples (optional) | `data/packed/luna_eval_predictions_<label>.jsonl` |
| Per-run eval artifacts (auto) | `data/processed/evals/<eval_id>/{metrics.json,predictions.jsonl}` |
| Experiment plan + results | `docs/engineering/assessments/dataset-quality-iterations.md` (append newest at **bottom**) |
| Historical pilot evidence | `docs/engineering/assessments/pilot-quality-iterations.md` (do not append general work) |
| Pack index | `data/packed/README.md` (add new files to the table) |

Never commit secrets. Metrics JSON is fine to commit. Live predictions may be large — prefer samples plus full metrics.

---

## Assessment protocol — quick reference

The normative, reproducible procedure is
[ASSESSMENT-PROTOCOL.md](ASSESSMENT-PROTOCOL.md). The sequence below is only a quick reference.
It applies to every quality-affecting change, not only pilot generation.

### 1. Pre-register the hypothesis and controls

Create a draft record in `dataset-quality-iterations.md`: one mechanism, primary metric, frozen
baseline, fixed seeds/provider/evaluator/scorer, regression gates, exact commands, and claim level.

### 2. Implement a minimal change

Allowed surfaces only (prompts, handoffs, template/logic, gate thresholds when intentional). Keep schema frozen.

### 3. Generate an isolated candidate

```bash
scripts/generate-dataset.sh \
  --n 12 --seeds-from 10000 --config <new-config> --agent-mode live
```

Never overwrite a baseline or pack unrelated processed runs. Requires Azure/GLM secrets for
`--agent-mode live`.

### 4. Assess narration + diversity **before** hardness

```bash
uv run cogito-mill assess \
  --local-dir data/packed/<config>.jsonl \
  --output data/packed/<config>_quality_metrics.json
```

If `passed` is false, **do not** run Luna as a success signal. Fix narration/diversity first.

### 5. Human-audit a deterministic stratified sample

Use the sample sizes and rubric in `QUALITY-METRICS.md`; record item IDs before review.

### 6. Evaluate hardness (main questions)

```bash
scripts/evaluate-dataset.sh \
  --local-dir data/packed/<config>.jsonl --config <config> --label <experiment>
```

Copies metrics into `data/packed/luna_eval_metrics_<label>.json`.

### 7. Compare and record

Complete the pre-registered section in
`docs/engineering/assessments/dataset-quality-iterations.md` using
[ASSESSMENT-RECORD-TEMPLATE.md](ASSESSMENT-RECORD-TEMPLATE.md). Include:

- Git, schema, dataset, evaluator prompt, and metrics hashes;
- exact generation/evaluation commands and provider identities;
- baseline, candidate, delta, threshold, and verdict for every required metric;
- human-audit sample and findings;
- failures, deviations, permissible claim, and next action.

Update `data/packed/README.md` when adding new pack files.

### 8. Decision rules

| Outcome | Action |
|---------|--------|
| Assess fail | Fix generation; do not claim hardness progress |
| Assess pass, main_accuracy >30% | Hardness fail — deepen structure without EMP walls |
| Assess pass, main_accuracy ≤30%, Wilson >30% | Dev gate only — scale pack before release claims |
| All gates pass at release size | Eligible for Hub publish consideration |

---

## How to evaluate each improvement

Treat each change as an experiment against the previous packed baseline.

1. **Isolate one mechanism.** Do not mix generator and measurement changes in one experiment.
2. **Hold the protocol fixed.** Use the same seeds, sample size/balance, provider/deployments,
   evaluator prompt, scorer, schema, and thresholds unless that variable is the experiment.
3. **Identify immutable inputs.** Record Git, schema, dataset, prompt, and metrics hashes.
4. **Compare gates, not vibes.**

| Dimension | Primary signal | Secondary |
|-----------|----------------|-----------|
| Readability | Assess `narration` + word range | Human read of 2–3 stories |
| Diversity | template/setting/stem/shingle gates | Family balance table |
| Answer form | `first_name_only_rate` | Exact-match vs variants |
| Hardness | `main_accuracy` | Wilson upper bound |
| Grounding | Generation accept rate / critic findings | Spot-check fact maps |

5. **Regression checks.** A “win” on hardness that reintroduces identifier dumps is a failure
   (iteration 0 lesson). A “win” on narration that yields 100% evaluator accuracy is incomplete.
6. **Match claims to sample regime.** Smoke, calibration, release-sized, and statistical release
   have distinct permissible claims in `QUALITY-METRICS.md`.
7. **Prefer structural hardness.** Lookup layers and linear checksums failed (iterations 3–4).
   Variable-depth nonlinear local concepts worked for calibration (iteration 7) but need diverse
   structural mechanisms at scale (state transitions, provenance DAGs, constraint worlds).

---

## Launch scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate-dataset.sh` | `generate-batch` → isolated pack → `assess` |
| `scripts/evaluate-dataset.sh` | Require passing assessment, then `evaluate --main-only` and snapshot metrics |
| `scripts/generate-pilot.sh` | Backward-compatible name for generation launcher |
| `scripts/evaluate-pilot.sh` | Backward-compatible name for evaluation launcher |

Both use `uv run`. See script `--help` / header comments for flags.

Manual CLI equivalents live in `data/packed/README.md`.

---

## Agent workflow checklist

When invoked for dataset quality work:

1. Complete the mandatory reading list at the top of this skill.
2. Pre-register experiment, controls, and permissible claim.
3. Confirm schemas will not change.
4. Choose one minimal improvement surface.
5. Run deterministic tests.
6. Generate isolated candidate → validate items → assess dataset → human audit → evaluate.
7. Compare baseline/candidate using every required metric.
8. Complete the append-only experiment record and update `data/packed/README.md`.
9. Commit code, retained metrics, hashes, and log together.

Do not invent provider keys. If secrets are missing, implement and test offline; leave live calibration for an environment with `AZURE_OPENAI_*` / `GLM_*`.
