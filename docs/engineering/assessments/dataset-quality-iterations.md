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

Status: planned
Claim level: development calibration
Protocol: dataset-quality.v1

### Hypothesis

Replacing iterated-checksum / status-scale ledgers with human-graspable timeline/alibi opportunity
(people, places, clock times, travel) plus anti-formulaic pack/critic/external-judge gates and a
two-phase story writer (fact spine → noise → coherent narration) will pass narration/diversity
including `no_formulaic_ledger`, keep story-only Luna main accuracy ≤ 0.30 on n=20, and recover
high appendix-assisted main accuracy (≥ 0.75 diagnostic).

### Scope and controls

- Change surfaces: concept formalizer mechanism; offline scaffold; story writer (two-phase);
  story critic / pack assessor formulaic+temporal gates; external judge rubric; appendix.v2
  timeline fields; prompts/roles
- Primary metric: assess pass with zero formulaic ledger hits; story-only main_accuracy ≤ 0.30
- Regression gates / invariants: Hub thin schema unchanged; appendix-assisted recovery diagnostic;
  no protocol/status/coefficient/modulo language in retained stories; n≥20 accepted items
- Baseline pack + SHA-256: `data/packed/pilot_v3_balanced.jsonl`
  (`2cfab656842f18db8ca5eeb4387811e63f588a553e53259c58929420b5d29c6b`)
- Candidate config / output path: `pilot_v4_timeline` under
  `data/experiments/quality-20260722-timeline-opportunity/` (retain to `data/packed/` on pass)
- Git SHA: (fill after commit)
- Thin/full schema SHA-256:
  thin `f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40`;
  full `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`
- Seed block/list: 11000–11019 (n=20)
- Requested size and balance: 20 accepted items; six timeline families rotating by seed
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer/judge/evaluator deployments: Cursor Cloud Azure defaults
- Prompt versions / evaluator prompt SHA-256: prompt_version `pilot.v4` (fill after run)
- Scorer version: pilot.v2
- Planned commands:
  - `scripts/generate-dataset.sh --n 20 --seeds-from 11000 --config pilot_v4_timeline --agent-mode live --output-root data/experiments/quality-20260722-timeline-opportunity`
  - story-only and appendix-assisted `cogito-mill evaluate`
  - external quality judge on retained pack evidence
- Known deviations: none planned

### Change

(pending measurement)

### Generation and item gates

(pending)

### Dataset metrics

(pending)

### Human audit

(pending)

### Difficulty evaluation

(pending)

### Verdict

(pending)

### Next action

Run live generation and complete the measured fields.
