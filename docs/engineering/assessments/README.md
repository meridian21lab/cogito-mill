# Dataset quality assessments

Append-only measurements for all Cogito Mill dataset-quality improvements. Pilot iterations are
the historical baseline, not the scope boundary.

| Doc | Purpose |
|-----|---------|
| [dataset-quality-iterations.md](dataset-quality-iterations.md) | Active pre-registered experiment log (newest at bottom) |
| [pilot-quality-iterations.md](pilot-quality-iterations.md) | Historical experiments establishing `pilot_v2` baseline |
| [skill](../../../.agents/skills/dataset-quality/SKILL.md) | Mandatory entry point and agent responsibilities |
| [metric registry](../../../.agents/skills/dataset-quality/QUALITY-METRICS.md) | Formulas, thresholds, diagnostics, sample regimes |
| [assessment protocol](../../../.agents/skills/dataset-quality/ASSESSMENT-PROTOCOL.md) | Reproducible end-to-end procedure |
| [record template](../../../.agents/skills/dataset-quality/ASSESSMENT-RECORD-TEMPLATE.md) | Pre-registration and baseline/candidate result format |

Launchers:

```bash
scripts/generate-dataset.sh --config <new-config> --output-root <clean-root>
scripts/evaluate-dataset.sh \
  --local-dir <clean-root>/packed/<new-config>.jsonl \
  --config <new-config> \
  --label <experiment-id>
```

Retained immutable packs and canonical metric snapshots live under `data/packed/`; raw run/eval
artifacts live under the selected output root and `data/processed/evals/`. Complete the mandatory
preflight in `AGENTS.md` before any quality-affecting work.
