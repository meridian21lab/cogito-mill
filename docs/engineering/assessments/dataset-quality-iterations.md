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

Status: running
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
  setting metadata; story prompts/critics; structural `n_hops` reporting; optional
  appendix-assisted evaluator path
- Primary metric: paired story-only vs appendix-assisted main accuracy (expect low unaided,
  high assisted); secondary: narration/diversity pass, counterfactual no longer checksum-retarget
- Regression gates / invariants: Hub thin schema unchanged; assess narration/diversity pass;
  story-only main_accuracy ≤ 0.30; transport_errors = 0; first_name_only_rate = 0; no
  `Name-2` gold answers; setting_family matches family setting
- Baseline pack + SHA-256: `data/packed/pilot_v2.jsonl`
  (`8eaebf7b108cda6d055bdd3db9ff4cd82f7e1eccba3012f41fbaea70d1df71b4` raw file;
  canonical dataset SHA-256 `866091c603495b2832ffb26e7ddda52d554fc58b157eb540abd167eae1ad0dbe`)
- Candidate config / output path: `pilot_v3_audit` under
  `data/experiments/quality-20260722-proof-carrying-evidence-cf/`
- Git SHA: (filled after commit)
- Thin/full schema SHA-256:
  `f89b79e30df8dded2d6f6c55f03f84a0cf521dd987345bbada86923f5d634e40` /
  `bfa5c6aaae4783906371cb7b6fff30c05feee39d91d96f3fd159525182544184`
- Seed block/list: 10000–10011 (n=12, same policy as pilot_v2 generation launcher defaults)
- Requested size and balance: 12 accepted items, six families via existing rotation
- Difficulty: very_hard
- Agent mode: live
- Provider family: azure
- Writer/judge/evaluator deployments: Cursor Cloud Azure defaults
- Prompt versions / evaluator prompt SHA-256: prompt_version `pilot.v3`; evaluator prompt recorded
  in metrics
- Scorer version: pilot.v2
- Planned commands:
  - `scripts/generate-dataset.sh --n 12 --seeds-from 10000 --config pilot_v3_audit --agent-mode live --output-root data/experiments/quality-20260722-proof-carrying-evidence-cf`
  - story-only:
    `scripts/evaluate-dataset.sh --local-dir …/pilot_v3_audit.jsonl --config pilot_v3_audit --label v3_audit_story`
  - appendix-assisted:
    `uv run cogito-mill evaluate --local-dir …/pilot_v3_audit.jsonl --appendix …/pilot_v3_audit_appendix.jsonl --main-only --question-types main counterfactual --min-assisted-accuracy 0.75 --config pilot_v3_audit`
- Known deviations: mechanism monoculture (iterated tally) retained deliberately for this
  auditability-focused experiment; new structural families deferred

### Change

Evidence-edit counterfactuals; solver appendix sidecar; unique names without numeric suffixes;
setting_family from family; combined status-scale fact; structural n_hops; narration prompt/critic
polish; appendix-assisted eval path.

### Generation and item gates

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| accepted / rejected / attempts | | | | record | |
| acceptance yield | | | | diagnostic | |
| repairs / failure reasons | | | | diagnostic | |
| schema validity | | | | 100% | |
| unique IDs | | | | 100% | |
| deterministic correctness / grounding | | | | 100% accepted rows | |

### Dataset metrics

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| narration pass rate | 1.0 | | | size-dependent | |
| exact duplicates | 0 | | | 0 | |
| template count / effective count / max share | 6 / 5.14 / 0.25 | | | size-dependent | |
| setting coverage / entropy | 5 / 0.943 | | | size-dependent | |
| unique openings | 1.0 | | | ≥0.80 | |
| question stems / max share | 12 / 0.083 | | | size-dependent | |
| pairwise 5-shingle P95 / max | 0.087 / 0.097 | | | P95 ≤0.65 | |
| structural hops | 1768–2200 | | | every item ≥10 | |

Candidate pack SHA-256:
Integrity report path + SHA-256:
Quality metrics path + SHA-256:

### Human audit

- Sampling rule: calibration stratified, one per family, lowest id
- Selected item IDs:
- Reviewer: cloud agent
- Passed:
- Failed:
- Findings:

### Difficulty evaluation

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| main correct / n | 2/12 | | | record | |
| main accuracy | 0.167 | | | ≤0.30 development | |
| one-sided Wilson upper 95% | 0.399 | | | ≤0.30 release | |
| appendix-assisted main accuracy | n/a | | | ≥0.75 diagnostic | |
| first-name-only rate | 0.0 | | | diagnostic; target 0 | |
| transport errors | 0 | | | 0 | |

Evaluation metrics path + SHA-256:
Predictions artifact:

### Verdict

- Primary hypothesis:
- Regressions:
- Permissible claim:
- What this does not establish:

### Next action

Run generation, assess, story-only Luna, appendix-assisted Luna; complete this record.
