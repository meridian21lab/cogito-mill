# Dataset quality iteration log

Append-only log for **all** measured Cogito Mill quality improvements, not only pilot pack
iterations. Newest experiment goes at the bottom.

Protocol: `.agents/skills/dataset-quality/ASSESSMENT-PROTOCOL.md`  
Metrics: `.agents/skills/dataset-quality/QUALITY-METRICS.md`  
Template: `.agents/skills/dataset-quality/ASSESSMENT-RECORD-TEMPLATE.md`

The historical experiments that established the current baseline remain in
`pilot-quality-iterations.md` (iterations 0–7). Treat `pilot_v2` as the current measured baseline
until a later record explicitly promotes a replacement.

## quality-20260722-proof-carrying-evidence-cf — Proof-carrying evidence-edit companion (2026-07-22)

Status: passed
Claim level: development calibration
Protocol: dataset-quality.v1

### Hypothesis

Replacing checksum-retarget counterfactuals with minimal evidence-status edits, emitting a
companion solver appendix (status matrix, checkpoints, gold steps, falsifier), aligning
`setting_family` with narrative family, and removing twin-name suffixes will improve auditability
and question diversity while preserving narration/diversity gates and story-only Luna hardness
(main_accuracy ≤ 0.30). Appendix-assisted evaluation should recover much higher main accuracy
than the story-only condition.

### Scope and controls

- Change surfaces: formal counterfactual construction; companion appendix artifact; naming;
  setting metadata; story prompts/critics; structural `n_hops` reporting; family seed rotation;
  optional appendix-assisted evaluator path
- Primary metric: paired story-only vs appendix-assisted main accuracy (expect low unaided,
  high assisted); secondary: narration/diversity pass, counterfactual no longer checksum-retarget
- Regression gates / invariants: Hub thin schema unchanged; assess narration/diversity pass;
  story-only main_accuracy ≤ 0.30; transport_errors = 0; first_name_only_rate = 0; no
  `Name-2` gold answers; setting_family matches family setting
- Baseline pack + SHA-256: `data/packed/pilot_v2.jsonl`
  (raw `8eaebf7b108cda6d055bdd3db9ff4cd82f7e1eccba3012f41fbaea70d1df71b4`;
  canonical dataset SHA-256 `866091c603495b2832ffb26e7ddda52d554fc58b157eb540abd167eae1ad0dbe`)
- Candidate config / output path: `pilot_v3_balanced` in `data/packed/`
  (first attempt `pilot_v3_audit` failed diversity and is retained as a failed candidate under
  `data/experiments/quality-20260722-proof-carrying-evidence-cf/packed/`)
- Git SHA: `45d2824babf19d8e1fe081a328843551ccb715c8` (generation); final record commit follows
- Thin/full schema SHA-256:
  `f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40` /
  `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`
- Seed block/list: 10000–10011 (n=12)
- Requested size and balance: 12 accepted items, six families via `seed % n_families`
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer/judge/evaluator deployments: Cursor Cloud Azure defaults
- Prompt versions / evaluator prompt SHA-256: prompt_version `pilot.v3`;
  story-only prompt SHA-256 `b54439bf7b3f284139b00825122588189aeb2ef130b75735a41d6b01ab3f30f1`;
  appendix-assisted prompt SHA-256 `137aab94839734958b0b16876ed7c5beebec9dea315fff222891660e981c4e70`
- Scorer version: pilot.v2
- Planned commands: executed as below
- Known deviations: mechanism monoculture (iterated tally) retained deliberately; first
  candidate `pilot_v3_audit` failed template/setting diversity before family-rotation fix

### Change

Evidence-edit counterfactuals; solver appendix sidecar; unique names without numeric suffixes;
setting_family from family; combined status-scale fact; structural n_hops; narration prompt/critic
polish; balanced family rotation; appendix-assisted eval path.

### Generation and item gates

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| accepted / rejected / attempts | 12 live (hist.) | 12 / 0 / 12 | yield 1.0 | record | pass |
| acceptance yield | — | 1.0 | — | diagnostic | pass |
| repairs / failure reasons | — | concept/story repairs within budget | — | diagnostic | pass |
| schema validity | 100% | 100% | 0 | 100% | pass |
| unique IDs | 100% | 100% | 0 | 100% | pass |
| deterministic correctness / grounding | 100% | 100% accepted rows | 0 | 100% | pass |

### Dataset metrics

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| narration pass rate | 1.0 | 1.0 | 0 | size-dependent | pass |
| exact duplicates | 0 | 0 | 0 | 0 | pass |
| template count / effective count / max share | 6 / 5.14 / 0.25 | 6 / 6.0 / 0.167 | +eff / −share | size-dependent | pass |
| setting coverage / entropy | 5 / 0.943 | 4 / 0.959 | −1 setting / +ent | size-dependent | pass |
| unique openings | 1.0 | 1.0 | 0 | ≥0.80 | pass |
| question stems / max share | 12 / 0.083 | 12 / 0.083 | 0 | size-dependent | pass |
| pairwise 5-shingle P95 / max | 0.087 / 0.097 | 0.087 / 0.110 | ~0 | P95 ≤0.65 | pass |
| structural hops | 1768–2200 | 33 | human-scale | every item ≥10 | pass |

Candidate pack SHA-256 (raw file): `2cfab656842f18db8ca5eeb4387811e63f588a553e53259c58929420b5d29c6b`  
Canonical dataset SHA-256: `ef6e43fc077f0c460e876fdcf09afe1e52bb458eebabbf7c59cbd39aa0aae02c`  
Integrity report: `data/packed/pilot_v3_balanced_integrity_metrics.json`  
(`e1d5fb870add2f76626c98a6133243fca04c501d5049d8c254f43f9048a1916f`)  
Quality metrics: `data/packed/pilot_v3_balanced_quality_metrics.json`  
(`e351322527320609349635e2a2266411a81a47747046d00ab7fad455d0f82456`)  
Appendix: `data/packed/pilot_v3_balanced_appendix.jsonl`  
(`6d774802c96c657b9041229a0fc355bf9f49a528b03190de66340c40c1a883e6`)

### Human audit

- Sampling rule: calibration stratified, one per family, lowest id
- Selected item IDs: `lss-concept-010003`, `010005`, `010000`, `010004`, `010002`, `010001`
- Reviewer: cloud agent
- Passed: setting/opening coherence; no `Name-2` suffixes; all CFs are evidence-status edits;
  n_hops=33; appendices present for every id
- Failed: none on sampled hard defects
- Findings: narration still uses dense status vocabulary (expected under current mechanism);
  openings match tagged settings (expedition/workplace/historical/speculative). Failed prior
  candidate `pilot_v3_audit` showed family clumping before rotation fix.

### Difficulty evaluation

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| main correct / n | 2/12 | 2/12 story-only | 0 | record | pass |
| main accuracy | 0.167 | 0.167 story-only | 0 | ≤0.30 development | pass |
| one-sided Wilson upper 95% | 0.399 | 0.399 | 0 | ≤0.30 release | fail (expected, n=12) |
| appendix-assisted main accuracy | n/a | 1.00 (12/12) | +0.833 | ≥0.75 diagnostic | pass |
| story-only CF accuracy | n/a | 0.25 (3/12) | — | diagnostic | record |
| appendix-assisted CF accuracy | n/a | 1.00 (12/12) | — | diagnostic | pass |
| first-name-only rate | 0.0 | 0.0 | 0 | diagnostic; target 0 | pass |
| transport errors | 0 | 0 | 0 | 0 | pass |

Evaluation metrics:
- `data/packed/luna_eval_metrics_v3_balanced_story.json`
- `data/packed/luna_eval_metrics_v3_balanced_appendix.json`
- `data/packed/luna_eval_metrics_v3_balanced_story_cf.json`
- `data/packed/luna_eval_metrics_v3_balanced_appendix_cf.json`

### Verdict

- Primary hypothesis: **confirmed**. Story-only main accuracy stayed at 16.7% (≤30%), while
  appendix-assisted main accuracy reached 100%. Evidence-edit CFs replaced checksum retargets;
  appendix-assisted CF accuracy also reached 100% vs 25% story-only.
- Regressions: none on assess gates, transport, or first-name-only rate. Setting coverage is 4
  (vs baseline 5) because family→setting mapping is intentional; still passes the ≥4 gate.
- Permissible claim: development-calibration pack `pilot_v3_balanced` meets narration/diversity
  and development hardness gates, and demonstrates proof-carrying appendix recoverability.
- What this does not establish: statistical release hardness; mechanism diversity beyond iterated
  tallies; human time/error study; Hub-published appendix schema.

### Next action

Promote `pilot_v3_balanced` as the measured forward candidate for further work. Next experiment
should add a second structural mechanism family (state transition / provenance DAG / constraint
world) without dropping appendix recoverability or story-only hardness.

## quality-20260722-timeline-opportunity — Timeline/alibi stories vs formula ledgers (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1

### Hypothesis

Replacing iterated-checksum / status-scale ledgers with human-graspable timeline/alibi opportunity
(people, places, clock times, travel) plus anti-formulaic pack/critic/external-judge gates and a
two-phase story writer (fact spine → noise → coherent narration) will pass narration/diversity
including `no_formulaic_ledger`, keep story-only main accuracy ≤ 0.30 on n=20, and recover
high appendix-assisted main accuracy (≥ 0.75 diagnostic).

### Scope and controls

- Change surfaces: concept formalizer mechanism; offline scaffold; story writer (two-phase);
  story critic / pack assessor formulaic+temporal gates; external judge rubric; appendix.v2
  timeline fields; prompts/roles; model critics advisory when code gates pass
- Primary metric: assess pass with zero formulaic ledger hits; story-only main_accuracy ≤ 0.30
- Regression gates / invariants: Hub thin schema unchanged; appendix-assisted recovery diagnostic;
  no protocol/status/coefficient/modulo language in retained stories; n≥20 accepted items
- Baseline pack + SHA-256: `data/packed/pilot_v3_balanced.jsonl`
  (`2cfab656842f18db8ca5eeb4387811e63f588a553e53259c58929420b5d29c6b`)
- Candidate config / output path: `pilot_v4_timeline` then `pilot_v4b_neutral` in `data/packed/`
- Git SHA: timeline pack `2506647`; neutral follow-up on branch tip
- Thin/full schema SHA-256:
  thin `f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40`;
  full `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`
- Seed blocks: `pilot_v4_timeline` 11000–11019; `pilot_v4b_neutral` 12000–12019
- Requested size and balance: 20 accepted items; six timeline families
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer/judge/evaluator deployments: Cursor Cloud Azure defaults
- Prompt versions: `pilot.v4`
- Scorer version: pilot.v2
- Planned commands: executed as recorded in generation logs
- Known deviations: one `pilot_v4_timeline` item needed a post-hoc sentence split for P95≤45;
  `pilot_v4b_neutral` removes explicit elimination phrasing in facts

### Change

Replaced checksum/status-scale formalizer with timeline opportunity (clocks, alibis, travel);
anti-formula gates in critic/assess/external judge; two-phase story writing; code decides on
acceptance; companion appendix carries timelines/eliminations; neutral-claim follow-up removes
“too late / too soon” giveaways.

### Generation and item gates

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| accepted / rejected / attempts | 12 live | v4: 20/0/20; v4b: 20/0/20 | yield 1.0 | record | pass |
| acceptance yield | — | 1.0 | — | diagnostic | pass |
| schema validity | 100% | 100% | 0 | 100% | pass |
| unique IDs | 100% | 100% | 0 | 100% | pass |
| deterministic correctness / grounding | 100% | 100% accepted rows | 0 | 100% | pass |

### Dataset metrics

| Metric | Baseline (`pilot_v3_balanced`) | `pilot_v4_timeline` | `pilot_v4b_neutral` | Gate | Verdict |
|--------|--------------------------------|---------------------|---------------------|------|---------|
| narration pass rate | 1.0 | 1.0 | 1.0 | size-dependent | pass |
| formulaic ledger failures | n/a (ledger mechanism) | 0 | 0 | 0 | pass |
| exact duplicates | 0 | 0 | 0 | 0 | pass |
| template count / effective / max share | 6 / 6.0 / 0.167 | 6 / 5.88 / 0.20 | 6 / 5.88 / 0.20 | size-dependent | pass |
| setting coverage / entropy | 4 / 0.959 | 5 / 0.959 | 5 / 0.978 | size-dependent | pass |
| unique openings | 1.0 | 1.0 | 1.0 | ≥0.80 | pass |
| pairwise 5-shingle P95 | 0.087 | 0.113 | 0.115 | ≤0.65 | pass |

Candidate packs:
- `data/packed/pilot_v4_timeline.jsonl` (raw `947d2d82…`, dataset `e219e5fd…`)
- `data/packed/pilot_v4b_neutral.jsonl` (raw `d8c5b869…`, dataset `cf8ff826…`)
Quality metrics:
- `data/packed/pilot_v4_timeline_quality_metrics.json` (`5dd6896d…`)
- `data/packed/pilot_v4b_neutral_quality_metrics.json` (`1de272d7…`)

### Human audit

- Sampling rule: one per family, lowest id (`pilot_v4b_neutral`)
- Selected item IDs: family representatives `lss-concept-012000`–`012005`
- Reviewer: cloud agent + external Azure judge (`gpt-5.6-terra-stories`)
- Passed: no protocol/status/coefficient/modulo ledger language; readable incident+timeline form
- Failed: travel-matrix recital monotony; explicit “whole stretch / only fair tests” rule language;
  atmosphere labeled as irrelevant
- Findings: external judge confirms formulaic-ledger fix and hardness failure; recommends
  near-miss timelines without exhaustive route tables or rule announcements

### Difficulty evaluation

| Metric | Baseline | `pilot_v4_timeline` | `pilot_v4b_neutral` | Gate | Verdict |
|--------|----------|---------------------|---------------------|------|---------|
| main correct / n | 2/12 | 20/20 story-only | 20/20 story-only | record | fail hardness |
| main accuracy | 0.167 | 1.00 | 1.00 | ≤0.30 development | fail |
| appendix-assisted main accuracy | 1.00 | 1.00 | n/a (story-only already 1.00) | ≥0.75 diagnostic | pass (vacuous) |
| first-name-only rate | 0.0 | 0.0 | 0.0 | diagnostic | pass |
| transport errors | 0 | 0 | 0 | 0 | pass |

Evaluation metrics:
- `data/packed/luna_eval_metrics_v4_timeline_story.json`
- `data/packed/luna_eval_metrics_v4_timeline_appendix.json`
- `data/packed/luna_eval_metrics_v4b_neutral_story.json`

### Verdict

- Primary hypothesis: **partially confirmed / overall failed**. Formulaic ledger language is
  eliminated (0 failures; assess pass on n=20), and stories read as timeline/alibi mysteries
  rather than status-scale procedures. Story-only hardness **failed** (main accuracy 1.00 ≫ 0.30)
  on both candidates—explicit clock+travel availability filters are too easy for the recorded
  Azure evaluator.
- Regressions: none on schema, transport, formulaic ban, or diversity gates.
- Permissible claim: `pilot_v4b_neutral` is a narration/diversity development pack without ledger
  language; it is **not** a hardness-passing calibration pack.
- What this does not establish: relative-time encoding hardness; near-miss density; CF evaluation
  on the neutral pack; human time/error study.

### Next action

Next experiment: near-miss timeline set without route-matrix recitals or “only fair tests” rule
statements; interleave travel inside witness accounts; require ≥2 ordinary observations per
elimination; evaluate main + CF. Do not promote `pilot_v4*` over `pilot_v3_balanced` for hardness
claims—promote only as the anti-ledger narration baseline.

## quality-20260722-provenance-custody-dag — Connected custody provenance (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

Replacing v4's separable opportunity filter with a connected custody-provenance DAG—where every
suspect has local opportunity and the answer is derived from shared container handoffs, evidence
grounded state transitions, and a final authorization record—will reduce story-only Luna main
accuracy from 1.00 to ≤0.30 without reintroducing formula ledgers. Removing any key proof clue
must prevent the same unique answer, demonstrating dependency rather than answer-atom injection.

### Scope and controls

- Change surfaces: formal world / structural mechanism; story and question rendering; proof
  appendix state trace; agent prompts required to narrate provenance rather than opportunity
- Primary metric: story-only Luna `main_accuracy` ≤0.30 on a balanced n=20 candidate
- Regression gates / invariants: frozen Hub schemas; schema/ID validity 100%; deterministic
  unique disclosure; key-clue ablation cannot retain the same unique answer; assess passes every
  narration/diversity gate; no formulaic ledger; no answer-specific `has_opportunity` seed;
  transport errors 0; first-name-only rate 0; counterfactual evidence edit has a deterministically
  different unique custodian; proof appendix recovers the answer
- Baseline pack + SHA-256: anti-ledger mechanism baseline
  `data/packed/pilot_v4b_neutral.jsonl`
  (`d8c5b86920680435c37b11d564966ec8ecddf044683a3ceb455bcbf6fb2dce01`);
  retained hardness baseline `pilot_v3_balanced`
  (`2cfab656842f18db8ca5eeb4387811e63f588a553e53259c58929420b5d29c6b`)
- Candidate config / output path: `pilot_v5_provenance` under
  `data/experiments/quality-20260722-provenance-custody-dag/packed/`, then retained under
  `data/packed/` only if integrity and assess pass
- Git SHA: `7cb3f8acafa14583035fd0ab47cb7b60813730f3` before implementation
- Thin/full schema SHA-256:
  `f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40` /
  `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`
- Seed block/list: 13000–13019
- Requested size and balance: 20 accepted items; six existing narrative families rotated by seed
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer deployment/model: `gpt-5.6-luna-stories`
- Judge deployment/model: `gpt-5.6-terra-stories`
- Evaluator deployment/model: `gpt-5.6-luna-stories`
- Prompt versions / evaluator prompt SHA-256: generator `pilot.v5`; evaluator unchanged
  (`b54439bf7b3f284139b00825122588189aeb2ef130b75735a41d6b01ab3f30f1`)
- Scorer version: pilot.v2
- Planned commands:
  `uv run pytest tests/unit -q`;
  `uv run pytest tests/integration -q`;
  `scripts/generate-dataset.sh --n 20 --seeds-from 13000 --config pilot_v5_provenance
  --agent-mode live --output-root
  data/experiments/quality-20260722-provenance-custody-dag`;
  schema validation and `assess` via that launcher;
  `scripts/evaluate-dataset.sh --local-dir data/packed/pilot_v5_provenance.jsonl
  --config pilot_v5_provenance --label v5_provenance_story`;
  counterfactual and appendix-assisted diagnostic evaluations after the main gate
- Known deviations: provider generation is nondeterministic despite fixed recipes; n=20 supports
  development calibration only; mechanism and the minimum prompt changes needed to narrate it
  move together, so this tests the complete provenance treatment rather than prompt causality

### Change

Added a proof-carrying custody DAG with 13 state snapshots, answer-independent transitions,
key-clue ablation, natural evidence-edit counterfactuals, and versioned provenance prompts.

### Generation and item gates

20 accepted / 0 rejected / 20 attempts; schema and IDs valid; every generated key clue passed
the original ablation check. The later v1.1 backfill correctly rejected all 20 stories because
the first implementation directly named the tracked token during every transfer.

### Dataset metrics

Original assessment passed surface gates (20/20 narration; six families; shingle P95 0.157), but
the v1.1 backfill failed narration 0/20, formulaic 20/20, and direct-transfer reset 20/20.

### Human audit

Fixed IDs 013000–013005. Failed: repeated “same custody line” / “seams in view” transaction
frames made a disguised ledger; 013000 and 013005 also invented unrelated named casts.

### Difficulty evaluation

Non-gating Luna diagnostic: 20/20 correct, main accuracy 1.00, transport errors 0.

### Verdict

- Primary hypothesis: rejected; the formal DAG still had a last-transfer semantic shortcut.
- Regressions: human narration and v1.1 shortcut gates failed.
- Permissible claim: failed mechanism diagnostic only; pack quarantined.
- What this does not establish: cross-model hardness, human completion time, or statistical
  release hardness

### Next action

Keep the diagnostic artifacts quarantined; test blind whole-content transfer next.

## quality-20260722-provenance-blind-transfer — Blind contents transfer refinement (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

Keeping the custody graph but replacing four explicit token-naming repacks with seven uninspected
whole-content transfers will remove the last-transfer shortcut and reduce story-only Luna main
accuracy from 1.00 to ≤0.30. Deterministically varied event frames, a no-extra-named-people prompt,
and new boilerplate/direct-transfer gates will also make all six fixed human-audit samples read as
stories rather than custody ledgers.

### Scope and controls

- Change surfaces: story realization of existing provenance transitions; connected depth from
  four to seven transfer cycles; deterministic critic and assessor measurement
- Primary metric: story-only Luna `main_accuracy` ≤0.30 on n=20
- Regression gates / invariants: all v5 formal invariants; each key proof atom remains
  ablation-necessary; zero direct tracked-token transfer resets; zero repeated custody boilerplate
  hits; no invented named cast in the fixed human sample; all assess gates pass
- Baseline pack + SHA-256: quarantined
  `data/experiments/quality-20260722-provenance-custody-dag/packed/pilot_v5_provenance.jsonl`
  (raw `47b526dd81b95864cce7087b1d480180b106f37da72b75f7ec7356a8dfd5c5b7`;
  canonical `48ce4eb99c5f58b447b62b815e5362ba70592c36245feda2d493248a0aa9fb8a`)
- Candidate config / output path: `pilot_v5b_provenance_blind` under
  `data/experiments/quality-20260722-provenance-blind-transfer/`
- Git SHA: implementation commit follows; starting branch commit `3845ae7`
- Thin/full schema SHA-256: unchanged
  (`f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40` /
  `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`)
- Seed block/list: 14000–14019
- Requested size and balance: 20 accepted items; six families
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer / judge / evaluator: `gpt-5.6-luna-stories` /
  `gpt-5.6-terra-stories` / `gpt-5.6-luna-stories`
- Prompt versions / evaluator prompt SHA-256: generator `pilot.v5`; evaluator unchanged
  (`b54439bf7b3f284139b00825122588189aeb2ef130b75735a41d6b01ab3f30f1`)
- Scorer version: pilot.v2
- Planned commands: unit/integration/lint/type checks; backfill v4b and v5 under v1.1;
  `scripts/generate-dataset.sh --n 20 --seeds-from 14000
  --config pilot_v5b_provenance_blind --agent-mode live
  --output-root data/experiments/quality-20260722-provenance-blind-transfer`;
  integrity/assess; fixed audit IDs 014000–014005; Luna main + CF + appendix diagnostics
- Known deviations: the two new deterministic failure signatures were selected after the fixed
  v5 human audit, so the measurement version changes from v1 to v1.1; baseline v4b and
  quarantined v5 will be backfilled. The code repair began immediately after the failure was
  identified, before this second record was written; no v5b data was generated or measured.

### Change

Changed token-naming repacks to seven blind whole-content transfers, varied deterministic event
frames, blocked extra named cast, and added v1.1 shortcut/boilerplate gates.

### Generation and item gates

20 accepted / 0 rejected / 20 attempts; schema, IDs, unique disclosure, ablation, and axis
invariants passed.

### Dataset metrics

Assessment passed: narration 20/20, words 824–949, zero formulaic/direct-transfer failures, six
families, effective count 5.882, unique openings 1.0, shingle P95 0.194.

### Human audit

Fixed IDs 014000–014005 removed the extra cast and direct reset, but remained bookkeeping-heavy
despite varied frames.

### Difficulty evaluation

Non-gating Luna diagnostic: 20/20 correct, main accuracy 1.00, transport errors 0.

### Verdict

- Primary hypothesis: rejected; seven serial state updates were still trivial for Luna.
- Regressions: human burden increased without hardness.
- Permissible claim: narration/shortcut repair only; not a hard benchmark.
- What this does not establish: cross-model or statistical release hardness

### Next action

Reject serial provenance as the main hardness path; move to relational constraint worlds.

## quality-20260722-relational-constraint-world — Narrative relational CSP (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

Replacing serial provenance replay with a six-person relational constraint world over bijective
objects, places, and ordered times will require joint search across competing worlds and reduce
story-only Luna main accuracy from 1.00 to ≤0.30. Z3 will derive the target owner without any
direct person↔target clue; every retained core clue must be target-necessary under ablation, and
removing any whole non-person axis must leave multiple target candidates.

### Scope and controls

- Change surfaces: new internal formal constraint theory and Z3 compiler; concept formalizer;
  story/question rendering; generic solver appendix
- Primary metric: story-only Luna main accuracy ≤0.30 on n=16
- Regression gates / invariants: frozen Hub schemas; Z3 satisfiable and unique target; no direct
  person↔target-object clue; every core clue target-necessary; object/place/time axis dependence;
  2–4 precise questions; narration/diversity and v1.1 shortcut gates pass; no tables, status
  scales, inventory dumps, or answer leaks; transport errors 0
- Baseline pack + SHA-256: failed
  `pilot_v5b_provenance_blind` (raw
  `1890d4caec4ae4f6f8ff19402c31defe62d2935d8a44c1febd25e0e58f516197`;
  canonical `775505b1da03303b67679a40526628c17f992f8d5d6cc84f4e703f541dd7efea`)
- Candidate config / output path: `pilot_v6_relational_csp` under
  `data/experiments/quality-20260722-relational-constraint-world/`
- Git SHA: implementation commit follows; starting branch commit `031af4c`
- Thin/full schema SHA-256: unchanged
  (`f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40` /
  `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`)
- Seed block/list: 15000–15015
- Requested size and balance: 16 accepted items; six narrative families
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer / judge / evaluator: `gpt-5.6-luna-stories` /
  `gpt-5.6-terra-stories` / `gpt-5.6-luna-stories`
- Prompt versions / evaluator prompt SHA-256: generator `pilot.v6`; evaluator unchanged
  (`b54439bf7b3f284139b00825122588189aeb2ef130b75735a41d6b01ab3f30f1`)
- Scorer version: pilot.v2
- Planned commands: deterministic unit/integration/lint/type checks; isolated n=16 generation;
  integrity and assess; fixed audit IDs `015000`–`015005`; Luna main-only, counterfactual if
  present, then appendix-assisted recoverability diagnostic
- Known deviations: n=16 is a directional mechanism calibration, not a release claim; it follows
  external-judge advice to reject provenance if Luna stayed at ≥14/16, while retaining the
  canonical stricter ≤0.30 development hardness gate

### Change

Added a deep Z3 constraint module over six-person object/place/time bijections, natural
exclusion/order/XOR clues, target-level clue ablation, axis-dependence checks, and solver appendix.

### Generation and item gates

16 accepted / 0 rejected / 16 attempts; schema/IDs valid; unique owner and target clue ablations
passed under the then-current owner-only contract.

### Dataset metrics

Assessment passed: narration 16/16, words 448–637, six families, effective count 5.818, unique
openings 1.0, shingle P95 0.061, zero formulaic/direct-transfer failures.

### Human audit

Fixed IDs 015000–015005 passed coherence, grounding, answer leak/form, and vocabulary checks;
middle paragraphs remained intentionally clue-dense.

### Difficulty evaluation

Luna: 6/16 correct (0.375), Wilson upper 0.578, transport errors 0. This materially improved on
provenance but missed the canonical ≤0.30 gate.

### Verdict

- Primary hypothesis: directional support, canonical gate failed.
- Regressions: none on measured surface/integrity gates.
- Permissible claim: promising mechanism calibration, not a promoted hard pack.
- What this does not establish: release-scale, cross-model, or human-panel hardness

### Next action

Calibrate target choice by irreducible cross-axis dependency rather than serial clue count.

## quality-20260722-max-dependency-target — Max-dependency CSP target selection (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

Holding the relational CSP generator, clue language, evaluator, and all gates fixed while selecting
the object whose irreducible target-proof uses the most clues will reduce Luna main accuracy from
6/16 (0.375) to ≤0.30 without adding clues, prose, or serial operations after target selection.

### Scope and controls

- Change surfaces: deterministic target selection only
- Primary metric: story-only Luna main accuracy ≤0.30 on n=16
- Regression gates / invariants: all v6 Z3, ablation, axis-dependence, schema, narration,
  diversity, answer-form, and transport gates; clue count remains 10–30; evaluator unchanged
- Baseline pack + SHA-256: `pilot_v6_relational_csp` (raw
  `b54d028126cc21024ffd538b6157e5449696ab46a5547f926db7c53a47b5d4ee`;
  canonical `41a5a5adac55c3420fb21508750944de23b65e66488a64754caf1a90772a30d8`)
- Candidate config / output path: `pilot_v6b_max_dependency` under
  `data/experiments/quality-20260722-max-dependency-target/`
- Git SHA: implementation follows; starting branch commit `baae391`
- Thin/full schema SHA-256: unchanged
- Seed block/list: 16000–16015
- Requested size and balance: 16 accepted items; six families
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer / judge / evaluator: `gpt-5.6-luna-stories` /
  `gpt-5.6-terra-stories` / `gpt-5.6-luna-stories`
- Prompt versions / evaluator prompt SHA-256: generator `pilot.v6`; evaluator unchanged
  (`b54439bf7b3f284139b00825122588189aeb2ef130b75735a41d6b01ab3f30f1`)
- Scorer version: pilot.v2
- Planned commands: full offline validation; isolated n=16 generation; integrity/assess; fixed
  audit IDs `016000`–`016005`; Luna main-only; appendix-assisted diagnostic if main gate passes
- Known deviations: Azure generation/evaluation nondeterminism; the target-selection computation
  is slower because all six possible target objects are minimized before one is chosen

### Change

Changed only target choice: minimize all six candidate-object proofs and select the largest
irreducible owner proof.

### Generation and item gates

16 accepted / 0 rejected / 16 attempts across exact seeds 16000–16015; one Azure stall after
16007 was terminated by PID and resumed exactly at 16008.

### Dataset metrics

Assessment passed: narration 16/16, words 465–740, six families, shingle P95 0.075, zero
formulaic/direct-transfer failures.

### Human audit

Fixed audit failed: 016001 invented six decorative objects and presented them as the formal
bijection axis, creating an ambiguous/contradictory story despite automated assess passing.

### Difficulty evaluation

Non-gating due human failure, but Luna reached 4/16 (0.25), development hardness pass; transport
errors 0.

### Verdict

- Primary hypothesis: hardness supported, overall candidate failed human audit.
- Regressions: ungrounded axis vocabulary in one fixed sample.
- Permissible claim: mechanism hardness diagnostic only; pack quarantined.
- What this does not establish: release-scale or cross-model hardness

### Next action

Lock writer vocabulary to formal people, objects, places, and times.

## quality-20260722-csp-vocabulary-lock — Exact CSP vocabulary lock (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

Holding max-dependency CSP worlds fixed while explicitly whitelisting the six formal people,
objects, places, and times in both writer phases will eliminate invented-axis contradictions in
the six-item human audit while preserving the candidate's measured hardness direction and all
automated gates.

### Scope and controls

- Change surfaces: constraint-story writer prompt only
- Primary metric: zero invented people/object/place/time axis members in the fixed human sample;
  story-only Luna main accuracy remains ≤0.30
- Regression gates / invariants: generator/Z3/target-selection code unchanged; all schema,
  ablation, axis-dependence, assess, narration, diversity, answer-form, and transport gates
- Baseline pack + SHA-256: quarantined `pilot_v6b_max_dependency` (raw
  `148e1d58c8c12c7b4b33c066534c7293b891810821f6c6dc73a1ef67c14a2c02`;
  canonical `ec0ad2ab01de12e1ea23bce4cc512578d2d769955a15b46194089919a166f01a`)
- Candidate config / output path: `pilot_v6c_vocabulary_locked` under
  `data/experiments/quality-20260722-csp-vocabulary-lock/`
- Git SHA: implementation follows; starting branch commit `5347914`
- Thin/full schema SHA-256: unchanged
- Seed block/list: 16000–16015 (paired formal worlds with v6b; new isolated live narrations)
- Requested size and balance: 16 accepted items; six families
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer / judge / evaluator: `gpt-5.6-luna-stories` /
  `gpt-5.6-terra-stories` / `gpt-5.6-luna-stories`
- Prompt versions / evaluator prompt SHA-256: generator remains `pilot.v6`; evaluator unchanged
- Scorer version: pilot.v2
- Planned commands: full offline validation; isolated generation (resume exact seeds after any
  transport stall); integrity/assess; fixed audit IDs `016000`–`016005`; Luna main-only;
  appendix-assisted diagnostic if all prior gates pass
- Known deviations: prompt-only live generations are nondeterministic; the v6b transport stalled
  after eight accepted items and was resumed at seed 16008 without changing the seed block

### Change

Added an exact formal-axis vocabulary whitelist to both constraint-story writer phases.

### Generation and item gates

16 accepted / 0 rejected / 16 attempts over paired seeds; one Azure stall after 16008 was resumed
exactly at 16009.

### Dataset metrics

Assessment passed: narration 16/16, words 484–707, six families, shingle P95 0.091, all shortcut
and diversity gates passed.

### Human audit

Fixed IDs 016000–016005 passed the vocabulary/coherence audit; no invented axis members.

### Difficulty evaluation

Luna 4/16 (0.25), development gate passed, transport errors 0. Frozen tuple audit then found only
11/16 complete target tuples unique, so auxiliary place/time answers were invalid in five items.

### Verdict

- Primary hypothesis: vocabulary and hardness confirmed; complete answer contract failed.
- Regressions: five underdetermined auxiliary QA answers.
- Permissible claim: rejected pack; owner-only hardness diagnostic remains valid.
- What this does not establish: release-scale or cross-model hardness

### Next action

Audit complete tuples, emit countermodels, and regenerate under a tuple-aware verifier.

## quality-20260722-full-target-tuple-audit — Frozen CSP answer-contract audit (2026-07-22)

Status: failed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

All three scored v6c answers—target owner, place, and time—are invariant across every satisfying
model of each frozen visible constraint theory, not merely consistent with the hidden generation
world.

### Scope and controls

- Change surfaces: deterministic constraint verifier only; no generator, prompt, data, or
  evaluator change
- Primary metric: exactly one `(person, place, time)` tuple for the queried object in every one
  of the 16 frozen appendices
- Regression gates / invariants: existing unique-owner, clue-ablation, axis-dependence, and all
  retained pack/eval hashes unchanged
- Baseline pack + SHA-256: `pilot_v6c_vocabulary_locked` (raw
  `5ec1cc8ae3f4209cee5c882f7a0197a0788dd37389fb4326facf4d3c22f9cf82`;
  canonical `907cf235a43b5ff487d28790d4c19ded50c1585f99a6639cdb81f30cab5b7949`)
- Candidate config / output path: frozen-pack audit; no new candidate
- Git SHA: verifier implementation follows; starting branch commit `f471cb3`
- Thin/full schema SHA-256: unchanged
- Seed block/list: frozen 16000–16015
- Requested size and balance: 16 frozen items
- Difficulty / agent mode / provider: unchanged; no generation call
- Evaluator: no new story-only call; retained Luna result 4/16
- Planned commands: unit tests for tuple enumeration; validate all 16 packed appendices against
  their main/intermediate/scalar gold answers; emit countermodels on any mismatch
- Known deviations: external judge raised this gate after the measured final pack; this audit can
  only confirm or reject that frozen pack, not repair it post hoc

### Change

Added `target_tuples()` enumeration and `scripts/audit-constraint-tuples.py`; no frozen data was
modified.

### Generation and item gates

Not applicable; frozen artifacts only.

### Dataset metrics

Frozen audit: 11/16 unique full tuples; five countermodels showed variable place or time while
owner remained fixed.

### Human audit

Unchanged fixed sample.

### Difficulty evaluation

Unchanged retained 4/16 story-only result.

### Verdict

- Primary hypothesis: rejected.
- Regressions: none; this measurement exposed a pre-existing contract defect.
- Permissible claim: v6c rejected; no complete-bundle quality claim.
- What this does not establish: human solve rate or release hardness

### Next action

Make generation/minimization/ablation tuple-aware and create a new immutable candidate.

## quality-20260722-tuple-unique-csp — Full-answer unique relational CSP (2026-07-22)

Status: passed
Claim level: development calibration
Protocol: dataset-quality.v1.1

### Hypothesis

Minimizing, selecting, and ablating relational constraints against the complete queried
`(person, place, time)` tuple will make every scored answer uniquely entailed while preserving
v6c's narration gates and Luna main accuracy ≤0.30.

### Scope and controls

- Change surfaces: constraint target uniqueness criterion only; vocabulary-locked writer retained
- Primary metric: 16/16 unique and gold-matching target tuples; Luna main accuracy ≤0.30
- Regression gates / invariants: no direct person↔object clue; every retained clue tuple-necessary;
  object/place/time axis ablations break tuple uniqueness; schema/assess/human audit/transport
- Baseline pack + SHA-256: rejected `pilot_v6c_vocabulary_locked` (raw
  `5ec1cc8ae3f4209cee5c882f7a0197a0788dd37389fb4326facf4d3c22f9cf82`;
  canonical `907cf235a43b5ff487d28790d4c19ded50c1585f99a6639cdb81f30cab5b7949`;
  tuple audit 11/16)
- Candidate config / output path: `pilot_v6d_tuple_unique` under
  `data/experiments/quality-20260722-tuple-unique-csp/`
- Git SHA: verifier/generator implementation `a7e89ad`; retained pack/metrics `0aab564`
- Thin/full schema SHA-256: unchanged
- Seed block/list: 16000–16015 (same hidden assignments; tuple-aware visible clue selection)
- Requested size and balance: 16 accepted items; six families
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer / judge / evaluator: `gpt-5.6-luna-stories` /
  `gpt-5.6-terra-stories` / `gpt-5.6-luna-stories`
- Prompt versions / evaluator prompt SHA-256: generator `pilot.v6`; evaluator unchanged
- Scorer version: pilot.v2
- Planned commands: full offline validation; isolated generation with exact-seed resume on stall;
  integrity/assess; tuple audit; fixed human IDs `016000`–`016005`; Luna main-only; appendix assist
- Known deviations: v6c main hardness remains a valid owner-question diagnostic but the pack is
  rejected because 5/16 auxiliary answers were underdetermined. The v6d Azure writer stalled
  after seed 16006; the exact process was terminated and generation resumed at 16007 without
  replacing or skipping any seed.

### Change

Changed target minimization, max-dependency selection, ablation, and axis checks from owner-only
to complete `(person, place, time)` tuple uniqueness. Added reusable frozen-pack tuple audit.

### Generation and item gates

16 accepted / 0 rejected / 16 attempts; one Azure stall after seed 16006 was terminated by exact
PID and resumed at 16007. Schema valid 16/16; IDs unique; tuple audit 16/16; every retained clue
and each object/place/time axis is tuple-necessary.

### Dataset metrics

Assessment passed: narration 16/16; words 466–723; zero duplicates, formulaic hits, or transfer
resets; six families; effective family count 5.818; max share 0.1875; setting entropy 0.972;
unique openings/stems 1.0; shingle P95 0.095.

- Pack raw / canonical SHA-256:
  `c4e87603f541a8cb803fcc92ad2fb0b1c7ff36d865d83bf0fa37269616b48975` /
  `43abc1f9513ee3972a4b51d0f690c5807048a259a96d7eb2f5e983aaae947ac9`
- Appendix SHA-256:
  `1a3528c2ee63a57394259028f19e5d3897822db98f3770ab7bcd5b09d5ed05cd`
- Integrity / quality / tuple-audit SHA-256:
  `9c078ba20f9994a82902dea79f191da94e199bb8e7a087d97448497f2928b42b` /
  `107ed57ccfba62c90795c788a44a0c33a0e84d2793df30f70b0c10129303f542` /
  `1283897ac9c34cd85a496100d6c9663a9c389aa12a09daf96d08cae50600b4b8`

### Human audit

Fixed IDs 016000–016005 passed: coherent case-file narration, exact formal vocabulary, no answer
leak, explicit answer forms, self-contained bijection rule, and plausible ordinary activity.

### Difficulty evaluation

Story-only Luna: 3/16 (0.1875), development hardness pass; Wilson upper 0.388 (release fail);
first-name-only 0; transport errors 0. Appendix-assisted Luna: 16/16, transport errors 0.
Metrics SHA-256 story / appendix:
`55820c8d1eebeea2172d7042f6389923cee5fa6d32f56ae1a94a13f33bd98e74` /
`6dfde442fd95afb8974935e5433204c16ff089288a1807a0b7316241f5db4d24`.

### Verdict

- Primary hypothesis: confirmed at development-calibration scope.
- Regressions: none on registered gates; complete tuple correctness repaired.
- Permissible claim: promote `pilot_v6d_tuple_unique` as a hard, readable, solver-verifiable
  development calibration against the recorded Luna snapshot.
- What this does not establish: release-scale or cross-model hardness
- External Azure judge (`gpt-5.6-terra-stories`): promote for development calibration only;
  release promotion blocked by Wilson upper 0.388 and missing blinded human solve traces.

### Next action

Promote for development calibration only. Next run a fresh release-sized holdout plus blinded
human solve traces; do not infer statistical release hardness from n=16.
