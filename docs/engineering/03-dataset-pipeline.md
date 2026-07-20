# Dataset pipeline (draft)

## Stages

1. **Design** — clue map, cast, secret, constraints  
2. **Generate** — long narrative + questions + gold reasoning  
3. **Verify** — answerability, uniqueness, no early leaks, schema  
4. **Package** — local artifacts under `data/processed/`  
5. **Publish** — Hugging Face Hub under `ksopyla/<name>`

## Local data layout

```text
data/
  raw/        # intermediate agent outputs
  interim/    # partially validated
  processed/  # release candidates
```

## Hugging Face

- Namespace default: `ksopyla` (`HF_DATASET_NAMESPACE`)
- Auth: `HF_TOKEN`
- Agent skill: `huggingface-datasets` (Dataset Viewer + upload guidance)
- Prefer Parquet / JSONL with a clear dataset card (to be specified)

## Schema

Canonical item schema will live in `schemas/` once grilled. Until then, treat fields as TBD in `04-open-questions.md`.
