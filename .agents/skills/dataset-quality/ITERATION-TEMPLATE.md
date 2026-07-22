# Iteration log template

Append a new section to `docs/engineering/assessments/pilot-quality-iterations.md`
(newest at the **bottom**). Fill every subsection.

```markdown
## Iteration N — <short title> (YYYY-MM-DD)

Source: `data/packed/<config>.jsonl` (N items),
`<config>_quality_metrics.json`, and `luna_eval_metrics_<label>.json`.

### Hypothesis

One sentence: what change should move which gate, without breaking others.

### What changed

1. …
2. …

### Narration and diversity

- Assess `passed`: true/false
- Narration: pass/fail counts; word min / median / max
- Exact duplicates:
- Families / settings / opening / stem metrics:
- Pairwise 5-shingle P95 / max:
- Per-story critic notes (if relevant):

### Luna main-question evaluation

- Correct: k/N
- Main accuracy: x% — development hardness gate (≤30%): passed/failed
- Wilson upper 95%: y% — statistical release gate (≤30%): passed/failed
- First-name-only rate:
- Transport errors:

### Honest verdict

- What succeeded
- What failed
- What this does *not* claim (e.g. calibration-only, single hardness mechanism)

### Next refinement

Concrete next experiment; assess gates first, then Luna.
```

## Minimal metrics checklist

Before marking an iteration complete, ensure these files exist:

- [ ] `data/packed/<config>.jsonl`
- [ ] `data/packed/<config>_quality_metrics.json`
- [ ] `data/packed/luna_eval_metrics_<label>.json` (if hardness was run)
- [ ] Section appended to `pilot-quality-iterations.md`
- [ ] `data/packed/README.md` table updated
