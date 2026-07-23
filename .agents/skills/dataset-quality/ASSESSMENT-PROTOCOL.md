# Reproducible dataset quality assessment protocol

Protocol version: **dataset-quality.v1.1**

`v1.1` adds the provenance direct-token-transfer reset gate and custody-boilerplate patterns after
the first v5 human audit showed that the prior narration/formulaic metrics missed those shortcuts.

Use this protocol for every change that can alter generated items, acceptance decisions, packed
dataset composition, evaluator inputs, scores, or quality claims. Documentation-only edits to
this protocol use the same preflight and validation, but do not require live generation.

## 0. Mandatory preflight

Before planning or editing, read:

1. `.agents/skills/dataset-quality/SKILL.md`
2. `.agents/skills/dataset-quality/QUALITY-METRICS.md`
3. this protocol
4. `docs/engineering/assessments/dataset-quality-iterations.md`
5. the latest relevant entries in
   `docs/engineering/assessments/pilot-quality-iterations.md`
6. `data/packed/README.md`
7. `schemas/reasoning-item.schema.json`
8. `schemas/reasoning-item-full.schema.json`

Then inspect the implementation paths affected by the proposed change. Do not rely on the docs
when code is the executable source for a gate.

## 1. Classify the change

Record all applicable surfaces:

- formal world / structural mechanism;
- evidence selection or grounding;
- agent prompt;
- agent handoff or repair feedback;
- internal agent / graph logic;
- story or question rendering;
- deterministic critic / quality threshold;
- scorer / evaluator prompt / provider;
- packing / schema projection / publication;
- documentation / protocol only.

If a quality threshold, formula, sample regime, scorer, or evaluator prompt changes, this is a
**measurement change**, not merely a generator improvement. Backfill the baseline under the new
measurement where possible.

## 2. Pre-register the experiment

Before implementation, add a draft entry to
`docs/engineering/assessments/dataset-quality-iterations.md` using
`ASSESSMENT-RECORD-TEMPLATE.md`. Assign:

- experiment ID: `quality-YYYYMMDD-<short-slug>`;
- hypothesis;
- primary metric and expected direction;
- invariants / regression gates;
- baseline pack;
- candidate config and non-overwriting output paths;
- generation seed block and requested size;
- provider family and writer/judge/evaluator identities;
- protocol, prompt, schema, and scorer versions;
- exact planned commands;
- smoke/calibration/release claim level.

This prevents selecting favorable metrics after seeing results.

## 3. Freeze baseline and candidate identity

Never overwrite a baseline pack or its metrics. Use a new config/label for each measured
candidate.

Record before running:

```bash
git rev-parse HEAD
sha256sum schemas/reasoning-item.schema.json schemas/reasoning-item-full.schema.json
sha256sum data/packed/<baseline>.jsonl
```

Use the same seed block, requested size, difficulty, provider family, agent mode, evaluator,
prompt, scorer, and quality thresholds for baseline/candidate comparisons unless the experiment
explicitly changes one. If any differ, state why and downgrade causal claims.

For live-model experiments, matching seeds controls recipe inputs but not provider
nondeterminism. Treat results as a measured run, not a proof that every rerun is identical.

## 4. Verify implementation offline

Run at minimum:

```bash
uv run pytest tests/unit -q
```

Run relevant integration/E2E tests when generation, graph routing, packing, or evaluation code
changes. Add deterministic regression tests for new formal mechanisms and gate behavior.

Do not weaken or delete a failing gate merely to obtain accepted output.

## 5. Generate an isolated candidate

Use a new candidate config and a clean output root; never pack unrelated historical
`data/processed` runs into the candidate.

```bash
scripts/generate-dataset.sh \
  --config <candidate> \
  --n 12 \
  --seeds-from <fixed-start> \
  --agent-mode live \
  --output-root <clean-run-root>
```

Capture:

- exact command and UTC time;
- requested/accepted/rejected/attempt counts;
- seed range/list;
- run manifests and critic findings;
- output pack path and SHA-256;
- provider/deployment identifiers (never credentials).

An `n=1` run is a smoke test only. Do not interpret its diversity gates.

## 6. Validate item integrity and deterministic gates

Before dataset metrics:

1. validate every packed row against the thin schema:
   `uv run python scripts/validate-packed-dataset.py <candidate.jsonl>
   --output <candidate>_integrity_metrics.json`;
2. verify unique IDs;
3. confirm accepted items have passing world, uniqueness, grounding, story, and final reports;
4. confirm all expected rows are present;
5. record generation yield and failure-reason counts.

`validate-packed-dataset.py` uses JSON Schema Draft 2020-12, rejects duplicate IDs, and records
raw-file, canonical-dataset, and schema SHA-256 values. `assess` does not replace schema
validation.

## 7. Run dataset assessment

```bash
uv run cogito-mill assess \
  --local-dir data/packed/<candidate>.jsonl \
  --output data/packed/<candidate>_quality_metrics.json
```

Verify:

- command exits 0;
- report `passed` is true;
- every named gate is present;
- report `n` equals packed row count;
- report `dataset_sha256` equals the integrity report;
- metrics file SHA-256 is recorded.

If assessment fails, stop the promotion path. You may continue diagnostics, but must label
hardness results **non-gating**; difficulty cannot rescue an invalid pack.

## 8. Perform the human audit

Use the deterministic stratified sampling rule in `QUALITY-METRICS.md`. Record selected item IDs,
reviewer, rubric result, and findings. Do not replace the sample after seeing a bad item.

When a human audit catches a severe defect that automated gates miss:

1. mark the candidate failed or quarantined;
2. add a regression test/gate when objectively expressible;
3. record the gap and repair in the same experiment entry.

## 9. Evaluate difficulty

Only a pack that passed integrity and dataset assessment may produce a gating hardness claim.

```bash
scripts/evaluate-dataset.sh \
  --local-dir data/packed/<candidate>.jsonl \
  --config <candidate> \
  --label <experiment-label>
```

Verify:

- full intended row coverage;
- main-only evaluation;
- `transport_errors == 0`;
- dataset hash equals the candidate;
- evaluator prompt hash and scorer version are recorded;
- observed main accuracy and one-sided Wilson upper bound are both reported.

Do not compare evaluation numbers across different providers, deployments, prompts, scorers, or
answer projections as if they were the same measurement.

## 10. Compare baseline and candidate

Create a compact table with baseline, candidate, absolute delta, gate, and verdict for:

- item correctness/grounding failures;
- narration pass rate and word/sentence diagnostics;
- every dataset diversity gate;
- generation yield and repair diagnostics;
- human-audit defects;
- main accuracy and Wilson upper bound;
- first-name-only rate and transport errors.

Interpretation rules:

1. Primary metric improves and every invariant passes → improvement supported at the declared
   sample regime.
2. Primary metric improves but any hard gate regresses → candidate fails.
3. Metric changed at the same time as generator → no clean causal comparison; backfill or split
   experiments.
4. Small-pack observed hardness passes but Wilson fails → development calibration only.
5. No measurable change → do not claim improvement.

## 11. Record and retain

Complete the draft entry in `dataset-quality-iterations.md`; never rewrite historical results.
Link:

- commit SHA;
- commands;
- immutable pack and metric paths;
- dataset/schema/prompt hashes;
- generated run/eval artifact directories;
- selected human-audit item IDs;
- failures and deviations;
- honest verdict and next experiment.

Update `data/packed/README.md` for every retained pack or canonical metric snapshot. Full live
predictions may remain in ignored `data/processed/evals`; commit metrics and a representative
sample when appropriate.

## 12. Required decision order

```text
schema/integrity
  → deterministic item correctness and grounding
  → narration and dataset diversity
  → human audit
  → model difficulty
  → statistical release claim
```

A later success never compensates for an earlier failure.

## Deviations

If secrets, provider access, or budget prevent a live phase:

- complete deterministic/offline phases;
- mark live metrics `not run`;
- do not copy old metrics onto the new candidate;
- do not claim a measured quality improvement;
- record the exact blocker and the command still required.
