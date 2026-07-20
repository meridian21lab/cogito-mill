# Long Story Short — pilot_v0 local pack

This directory holds the **pilot slice** release artifacts while Hugging Face Hub
publish is blocked on a write-capable `HF_TOKEN`.

| File | Purpose |
|------|---------|
| `pilot_v0.jsonl` | 150 thin Hub-schema items |
| `luna_eval_metrics.json` | Blind Azure Luna eval summary |
| `luna_eval_predictions_sample.jsonl` | Per-item predictions for the scored sample |

## Schema (simple)

Each JSONL row:

- `id`
- `story`
- `question`
- `gold_answer`
- `n_hops`
- `setting_family`
- `difficulty_bucket`

## Load locally

```python
import json
from pathlib import Path

rows = [
    json.loads(line)
    for line in Path("data/packed/pilot_v0.jsonl").read_text().splitlines()
    if line.strip()
]
print(rows[0]["question"], "->", rows[0]["gold_answer"])
```

Or via Hugging Face `datasets` from JSONL:

```python
from datasets import load_dataset

ds = load_dataset("json", data_files="data/packed/pilot_v0.jsonl", split="train")
print(ds[0]["story"][:200])
```

## Evaluate (Luna)

```bash
uv run cogito-mill evaluate \
  --local-dir data/packed/pilot_v0.jsonl \
  --solver-provider azure \
  --limit 50
```

Latest recorded exact-answer accuracy on a 50-item sample: **0.0** (hardness gate ≤30% passed).

## Publish to Hub (when token allows)

Requires a token that can **create/write** datasets under `ksopyla` (current cloud
secret `repositories_read_token` is read-only).

```bash
uv run cogito-mill publish \
  --input data/processed \
  --repo ksopyla/long-story-short-pilot \
  --config pilot_v0 \
  --private
```

If `data/processed/run-*` is absent locally, regenerate first:

```bash
uv run cogito-mill generate-batch --n 150 --seeds-from 5000 --difficulty very_hard
```
