# Pilot quality assessments

Living measurements against packed Long Story Short pilots.

| Doc | Purpose |
|-----|---------|
| [pilot-quality-iterations.md](pilot-quality-iterations.md) | Iteration log (newest at bottom) |
| [../../.agents/skills/dataset-quality/SKILL.md](../../.agents/skills/dataset-quality/SKILL.md) | **Canonical protocol**: gates, recording locations, agents, schema freeze |
| [../../.agents/skills/dataset-quality/ITERATION-TEMPLATE.md](../../.agents/skills/dataset-quality/ITERATION-TEMPLATE.md) | Section template for each iteration |

Launchers:

```bash
scripts/generate-pilot.sh
scripts/evaluate-pilot.sh --local-dir data/packed/pilot_v2.jsonl --label v2
```

Metrics and packs live under `data/packed/`. Read the skill before changing generation or evaluation.
