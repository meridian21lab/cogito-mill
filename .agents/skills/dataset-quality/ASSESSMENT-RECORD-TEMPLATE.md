# Dataset quality experiment record template

Append this record to
`docs/engineering/assessments/dataset-quality-iterations.md`. Create the hypothesis and planned
controls **before** implementation; complete measured fields after evaluation.

```markdown
## <experiment-id> — <short title> (<YYYY-MM-DD>)

Status: planned | running | passed | failed | inconclusive | blocked
Claim level: smoke | development calibration | release candidate | statistical release
Protocol: dataset-quality.v1

### Hypothesis

<One mechanism, primary metric, expected direction.>

### Scope and controls

- Change surfaces:
- Primary metric:
- Regression gates / invariants:
- Baseline pack + SHA-256:
- Candidate config / output path:
- Git SHA:
- Thin/full schema SHA-256:
- Seed block/list:
- Requested size and balance:
- Difficulty:
- Agent mode:
- Provider family:
- Writer deployment/model:
- Judge deployment/model:
- Evaluator deployment/model:
- Prompt versions / evaluator prompt SHA-256:
- Scorer version:
- Planned commands:
- Known deviations:

### Change

<Files/behavior changed; do not paste implementation detail.>

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
| narration pass rate | | | | size-dependent | |
| exact duplicates | | | | 0 | |
| template count / effective count / max share | | | | size-dependent | |
| setting coverage / entropy | | | | size-dependent | |
| unique openings | | | | ≥0.80 | |
| question stems / max share | | | | size-dependent | |
| pairwise 5-shingle P95 / max | | | | P95 ≤0.65 | |
| structural hops | | | | every item ≥10 | |

Candidate pack SHA-256:
Integrity report path + SHA-256:
Quality metrics path + SHA-256:

### Human audit

- Sampling rule:
- Selected item IDs:
- Reviewer:
- Passed:
- Failed:
- Findings:

### Difficulty evaluation

| Metric | Baseline | Candidate | Delta | Gate | Verdict |
|--------|----------|-----------|-------|------|---------|
| main correct / n | | | | record | |
| main accuracy | | | | ≤0.30 development | |
| one-sided Wilson upper 95% | | | | ≤0.30 release | |
| first-name-only rate | | | | diagnostic; target 0 | |
| transport errors | | | | 0 | |

Evaluation metrics path + SHA-256:
Predictions artifact:

### Verdict

- Primary hypothesis:
- Regressions:
- Permissible claim:
- What this does not establish:

### Next action

<Promote, reject, quarantine, replicate, or run one named next experiment.>
```
