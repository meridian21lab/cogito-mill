# Long Story Short — retained packed datasets

This directory indexes immutable retained packs and canonical metric snapshots. Never overwrite a
baseline; add a new config/label for every measured candidate.

Required protocol: `.agents/skills/dataset-quality/ASSESSMENT-PROTOCOL.md`.
Metric definitions: `.agents/skills/dataset-quality/QUALITY-METRICS.md`.
Active log: `docs/engineering/assessments/dataset-quality-iterations.md`.
Historical pilot log: `docs/engineering/assessments/pilot-quality-iterations.md`.

| File | Purpose |
|------|---------|
| `pilot_v0.jsonl` | Original 150-item pack (low readability; EMP-wall style) |
| `pilot_v1.jsonl` | Improved 150-item pack (coherent narration, 2–4 QAs, answer variants) |
| `pilot_v2.jsonl` | 12-item live-agent calibration pack (six concept families, nonlinear local rules) |
| `pilot_v2_integrity_metrics.json` | Schema, unique-ID, dataset, and schema hashes for `pilot_v2` |
| `pilot_v2_quality_metrics.json` | Narration and pack-level diversity gates for `pilot_v2` |
| `pilot_v3_balanced.jsonl` | 12-item calibration pack with evidence-edit CFs + structural hops |
| `pilot_v3_balanced_appendix.jsonl` | Companion solver appendix (not Hub thin schema) |
| `pilot_v3_balanced_integrity_metrics.json` | Integrity hashes for `pilot_v3_balanced` |
| `pilot_v3_balanced_quality_metrics.json` | Narration/diversity gates for `pilot_v3_balanced` |
| `pilot_v4_timeline.jsonl` | 20-item timeline/alibi pack (anti-ledger; hardness fail) |
| `pilot_v4_timeline_appendix.jsonl` | Timeline opportunity appendix for `pilot_v4_timeline` |
| `pilot_v4_timeline_integrity_metrics.json` | Integrity hashes for `pilot_v4_timeline` |
| `pilot_v4_timeline_quality_metrics.json` | Narration/diversity gates for `pilot_v4_timeline` |
| `pilot_v4b_neutral.jsonl` | 20-item neutral-claim timeline pack (anti-ledger; hardness fail) |
| `pilot_v4b_neutral_appendix.jsonl` | Timeline opportunity appendix for `pilot_v4b_neutral` |
| `pilot_v4b_neutral_integrity_metrics.json` | Integrity hashes for `pilot_v4b_neutral` |
| `pilot_v4b_neutral_quality_metrics.json` | Narration/diversity gates for `pilot_v4b_neutral` |
| `luna_eval_metrics.json` | Luna eval on `pilot_v0` |
| `luna_eval_metrics_v1.json` | Luna eval sample on `pilot_v1` |
| `luna_eval_metrics_v2.json` | Luna main-question eval on `pilot_v2` |
| `luna_eval_metrics_v3_balanced_story.json` | Story-only Luna main eval on `pilot_v3_balanced` |
| `luna_eval_metrics_v3_balanced_appendix.json` | Appendix-assisted Luna main eval |
| `luna_eval_metrics_v3_balanced_story_cf.json` | Story-only counterfactual eval |
| `luna_eval_metrics_v3_balanced_appendix_cf.json` | Appendix-assisted counterfactual eval |
| `luna_eval_metrics_v4_timeline_story.json` | Story-only main eval on `pilot_v4_timeline` (1.00) |
| `luna_eval_metrics_v4_timeline_appendix.json` | Appendix-assisted main eval on `pilot_v4_timeline` |
| `luna_eval_metrics_v4b_neutral_story.json` | Story-only main eval on `pilot_v4b_neutral` (1.00) |
| `luna_eval_predictions_sample.jsonl` | `pilot_v0` prediction sample |
| `luna_eval_predictions_v1_sample.jsonl` | `pilot_v1` prediction sample |

## Schema (`pilot_v2`)

Each JSONL row:

- `id`
- `story`
- `question` — main mystery (also first of `questions`)
- `gold_answer`
- `gold_answer_variants` — 1–3 accepted exact-match forms
- `questions` — 2–4 scored QAs (`id`, `question`, `gold_answer`, `gold_answer_variants`, `question_type`)
- `n_hops`
- `setting_family`
- `difficulty_bucket`
- `template_id`

## Load locally

```python
import json
from pathlib import Path

rows = [
    json.loads(line)
    for line in Path("data/packed/pilot_v2.jsonl").read_text().splitlines()
    if line.strip()
]
print(rows[0]["question"], "->", rows[0]["gold_answer"])
print(len(rows[0]["questions"]), "scored questions")
```

## Evaluate (Luna)

Preferred:

```bash
scripts/evaluate-dataset.sh \
  --local-dir data/packed/<candidate>.jsonl \
  --config <candidate> \
  --label <new-experiment-label>
```

Equivalent CLI:

```bash
uv run cogito-mill evaluate \
  --local-dir data/packed/pilot_v2.jsonl \
  --solver-provider azure \
  --limit 12 \
  --main-only
```

Hardness gate uses **main-question** exact-match accuracy (≤30%). `pilot_v2`
must also pass `cogito-mill assess`; hardness cannot compensate for failed
narration or diversity. The 12-item calibration result is **2/12 (16.7%)**;
its Wilson upper bound does not yet certify a release-sized benchmark. See
`docs/engineering/assessments/pilot-quality-iterations.md`.

## Regenerate

Preferred:

```bash
scripts/generate-dataset.sh \
  --n 12 \
  --seeds-from <fixed-start> \
  --config <new-candidate> \
  --agent-mode live \
  --output-root <clean-run-root>
```

Equivalent CLI:

```bash
uv run cogito-mill generate-batch \
  --n 12 --seeds-from 10000 --difficulty very_hard --agent-mode live
uv run cogito-mill publish --input data/processed --dry-run --config pilot_v2
uv run cogito-mill assess \
  --local-dir data/packed/pilot_v2.jsonl \
  --output data/packed/pilot_v2_quality_metrics.json
```
