# Long Story Short — packed pilots

| File | Purpose |
|------|---------|
| `pilot_v0.jsonl` | Original 150-item pack (low readability; EMP-wall style) |
| `pilot_v1.jsonl` | Improved 150-item pack (coherent narration, 2–4 QAs, answer variants) |
| `pilot_v2.jsonl` | 12-item live-agent calibration pack (six concept families, nonlinear local rules) |
| `pilot_v2_quality_metrics.json` | Narration and pack-level diversity gates for `pilot_v2` |
| `luna_eval_metrics.json` | Luna eval on `pilot_v0` |
| `luna_eval_metrics_v1.json` | Luna eval sample on `pilot_v1` |
| `luna_eval_metrics_v2.json` | Luna main-question eval on `pilot_v2` |
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

```bash
uv run cogito-mill generate-batch \
  --n 12 --seeds-from 10000 --difficulty very_hard --agent-mode live
uv run cogito-mill publish --input data/processed --dry-run --config pilot_v2
uv run cogito-mill assess --local-dir data/packed/pilot_v2.jsonl
```
