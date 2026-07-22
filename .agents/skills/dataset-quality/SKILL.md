---
name: dataset-quality
description: Develop and assess Long Story Short pilot datasets. Use when iterating on generation quality, measuring narration/diversity/hardness, recording assessments, evaluating improvements, or launching generate/evaluate scripts.
---

# Dataset quality — Long Story Short

Single reference for **further developing** the pilot reasoning dataset. Read this skill before changing generation, critics, prompts, or evaluation. After every measured change, append the iteration to
`docs/engineering/assessments/pilot-quality-iterations.md`.

Companion materials:

| Path | Role |
|------|------|
| `data/packed/README.md` | Packed pilots, load/eval/regenerate commands |
| `data/packed/` | Frozen packs, quality metrics, Luna metrics |
| `docs/engineering/assessments/pilot-quality-iterations.md` | Living assessment log (newest at bottom) |
| `schemas/reasoning-item.schema.json` | Hub thin item schema (**do not modify**) |
| `schemas/reasoning-item-full.schema.json` | Full accepted projection (**do not modify**) |
| `scripts/generate-pilot.sh` | Launch batch generation + pack + assess |
| `scripts/evaluate-pilot.sh` | Launch Luna hardness evaluation |

---

## Non-negotiables

1. **Keep the Hub schema.** Do not change fields, enums, or required keys in `schemas/`. Pack and eval must stay compatible with `pilot_v2` rows.
2. **Agents propose; code decides.** Models write premises, prose, and critiques. Z3/causal uniqueness, deterministic story gates, and pack assessors decide acceptance.
3. **Readability is not traded for hardness.** Identifier dumps and EMP walls are failures even if Luna accuracy falls.
4. **Minor agent changes only.** Prefer prompt, handoff, and internal-logic improvements over new graph topology or role proliferation.
5. **Hardness cannot compensate for failed narration or diversity.** Run `assess` before Luna; if assess fails, stop and fix the pack.

---

## Current baseline

| Artifact | Meaning |
|----------|---------|
| `data/packed/pilot_v2.jsonl` | 12-item live-agent calibration pack (six families, nonlinear local concept) |
| `data/packed/pilot_v2_quality_metrics.json` | Pack narration + diversity gates (passed) |
| `data/packed/luna_eval_metrics_v2.json` | Luna main-question hardness (16.7% = passed development gate) |

Historical packs (`pilot_v0`, `pilot_v1`) and their Luna metrics remain for regression narrative only. Iterate **forward** from `pilot_v2` lessons: see iterations 0–7 in the assessment log.

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
| Packed items | `data/packed/<config>.jsonl` (e.g. `pilot_v2.jsonl`) |
| Pack quality metrics | `data/packed/<config>_quality_metrics.json` |
| Luna / solver metrics (canonical snapshot) | `data/packed/luna_eval_metrics_<label>.json` |
| Luna prediction samples (optional) | `data/packed/luna_eval_predictions_<label>.jsonl` |
| Per-run eval artifacts (auto) | `data/processed/evals/<eval_id>/{metrics.json,predictions.jsonl}` |
| Iteration narrative + verdict | `docs/engineering/assessments/pilot-quality-iterations.md` (append newest at **bottom**) |
| Pack index | `data/packed/README.md` (add new files to the table) |

Never commit secrets. Metrics JSON is fine to commit. Live predictions may be large — prefer samples plus full metrics.

---

## Assessment protocol

Use this protocol for **every** quality iteration.

### 1. State the hypothesis

One sentence: what structural or narrative change should improve which gate, without breaking others.

### 2. Implement a minimal change

Allowed surfaces only (prompts, handoffs, template/logic, gate thresholds when intentional). Keep schema frozen.

### 3. Generate

```bash
scripts/generate-pilot.sh
# or with overrides:
scripts/generate-pilot.sh --n 12 --seeds-from 10000 --config pilot_v3 --agent-mode live
```

Defaults target a live calibration pack. Requires Azure/GLM secrets for `--agent-mode live`.

### 4. Assess narration + diversity **before** hardness

```bash
uv run cogito-mill assess \
  --local-dir data/packed/<config>.jsonl \
  --output data/packed/<config>_quality_metrics.json
```

If `passed` is false, **do not** run Luna as a success signal. Fix narration/diversity first.

### 5. Evaluate hardness (main questions)

```bash
scripts/evaluate-pilot.sh --local-dir data/packed/<config>.jsonl --label v3
```

Copies metrics into `data/packed/luna_eval_metrics_<label>.json`.

### 6. Record the iteration

Append a section to `docs/engineering/assessments/pilot-quality-iterations.md` using the template in [ITERATION-TEMPLATE.md](ITERATION-TEMPLATE.md). Include:

- hypothesis and what changed
- narration/diversity metrics (gate pass/fail)
- Luna main accuracy, Wilson upper bound, first-name-only rate
- honest verdict (what worked / failed)
- next refinement targets

Update `data/packed/README.md` when adding new pack files.

### 7. Decision rules

| Outcome | Action |
|---------|--------|
| Assess fail | Fix generation; do not claim hardness progress |
| Assess pass, main_accuracy >30% | Hardness fail — deepen structure without EMP walls |
| Assess pass, main_accuracy ≤30%, Wilson >30% | Dev gate only — scale pack before release claims |
| All gates pass at release size | Eligible for Hub publish consideration |

---

## How to evaluate each improvement

Treat each change as an experiment against the previous packed baseline.

1. **Isolate one mechanism.** Do not mix narration rewrites with hardness mechanisms in the same unlogged change.
2. **Hold the protocol fixed.** Same solver provider (Azure writer/Luna), `--main-only`, same scorer version, full prediction coverage (no silent skips).
3. **Compare gates, not vibes.**

| Dimension | Primary signal | Secondary |
|-----------|----------------|-----------|
| Readability | Assess `narration` + word range | Human read of 2–3 stories |
| Diversity | template/setting/stem/shingle gates | Family balance table |
| Answer form | `first_name_only_rate` | Exact-match vs variants |
| Hardness | `main_accuracy` | Wilson upper bound |
| Grounding | Generation accept rate / critic findings | Spot-check fact maps |

4. **Regression checks.** A “win” on hardness that reintroduces identifier dumps is a failure (iteration 0 lesson). A “win” on narration that yields 100% Luna (iteration 1–2) is incomplete.
5. **Prefer structural hardness.** Lookup layers and linear checksums failed (iterations 3–4). Variable-depth nonlinear local concepts worked for calibration (iteration 7) but need **diverse structural mechanisms** at scale (state transitions, provenance DAGs, constraint worlds).

---

## Launch scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate-pilot.sh` | `generate-batch` → dry-run `publish` into `data/packed/<config>.jsonl` → `assess` |
| `scripts/evaluate-pilot.sh` | `evaluate --main-only` on a packed JSONL; snapshot metrics into `data/packed/` |

Both use `uv run`. See script `--help` / header comments for flags.

Manual CLI equivalents live in `data/packed/README.md`.

---

## Agent workflow checklist

When invoked for dataset development:

1. Read the latest section of `pilot-quality-iterations.md` and `data/packed/README.md`.
2. Confirm schemas will not change.
3. Choose a minimal improvement surface (prompt / handoff / template logic / gate).
4. Run unit tests offline: `uv run pytest tests/unit -q`.
5. Generate → assess → evaluate via scripts (live only with secrets).
6. Append the iteration log and update `data/packed/README.md`.
7. Commit metrics + log with the code change.

Do not invent provider keys. If secrets are missing, implement and test offline; leave live calibration for an environment with `AZURE_OPENAI_*` / `GLM_*`.
