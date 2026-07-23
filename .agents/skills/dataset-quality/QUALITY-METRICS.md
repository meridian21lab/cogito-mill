# Dataset quality metric registry

This registry defines what Cogito Mill means by dataset quality. It applies to every
generation-quality change: prompts, handoffs, agent logic, formal worlds, evidence selection,
story rendering, question rendering, validation, scoring, packing, and release calibration.

The registry separates:

- **hard gates** — a failure blocks item acceptance or dataset promotion;
- **diagnostics** — always record and compare, but no threshold is currently justified;
- **claims gates** — constrain what can be claimed about a calibration or release.

Do not silently change a formula, threshold, scorer, evaluator prompt, or sample regime. Such a
change creates a new protocol version and must be called out in the assessment record.

## Measurement levels

| Level | Unit | Purpose |
|-------|------|---------|
| Item | One accepted/rejected story | Correctness, grounding, readability, QA contract |
| Batch | One generation run | Yield, repair behavior, failure modes |
| Dataset | One immutable packed JSONL | Integrity, coverage, diversity |
| Evaluation | Dataset × evaluator × prompt × scorer | Difficulty and answer-form behavior |
| Release | One or more evaluation replications | Statistical claim with uncertainty |

## Metric registry

### A. Integrity and reproducibility

| ID | Metric | Definition | Gate |
|----|--------|------------|------|
| `integrity.schema_valid` | Schema validity | `validate-packed-dataset.py` validates every row with JSON Schema Draft 2020-12 against the unchanged thin Hub contract; processed items validate against the full contract | 100% |
| `integrity.unique_ids` | Unique item IDs | `count(distinct id) / n` | 1.0 |
| `integrity.dataset_sha256` | Dataset identity | SHA-256 of canonical sorted-key JSON rows joined by newline | Record |
| `integrity.provenance_complete` | Reproduction metadata | Git SHA, protocol version, command, seed range/list, provider/model roles, prompt/scorer versions, schema hashes, requested/accepted/rejected counts | 100% for a release claim |
| `integrity.coverage` | Evaluator coverage | Predictions produced / requested scored units | 1.0; transport errors = 0 |

The assessor and evaluator record the canonical dataset hash; the integrity validator records
raw-file, canonical-dataset, and schema hashes. Generation provenance is distributed across run
manifests; the assessment record must collect the exact command, Git SHA, seed policy, and
provider/deployment identifiers.

### B. Deterministic item correctness

| ID | Source | Pass condition |
|----|--------|----------------|
| `logic.world_satisfiable` | `WorldSolver.analyze_world` | World is satisfiable |
| `logic.visible_unique` | `WorldSolver.analyze_disclosure` | Visible theory entails exactly one answer |
| `grounding.required_fact` | `required_fact_grounding` | Every required visible fact is sentence-anchored |
| `grounding.single_realization` | `single_fact_realization` | Each required fact is assigned to one scene |
| `grounding.known_obligations` | `known_scene_obligations` | Every scene obligation names a known fact |
| `item.story_critic` | Combined deterministic, grounding, and model reports | All accept |
| `item.final_critic` | Final usability critic | Accept; model opinion cannot override deterministic arithmetic |

All are item-level hard gates. Failed items are repaired within the bounded budget or rejected;
they are never packed as accepted rows.

### C. Item readability and QA contract

Current deterministic generation gates:

| Gate ID | Formula / threshold |
|---------|---------------------|
| `narrative_paragraphs` | Non-empty paragraphs ≥4 |
| `identifier_budget` | `EMP-\d+` token count ≤14 |
| `no_personnel_dump` | `Personnel index:` count ≤2 |
| `no_id_resolution_wall` | EMP “resolves to” clauses ≤3 |
| `question_count` | 2–4 scored questions |
| `answer_form_clarity` | Name-answer questions explicitly request the full name |
| `answer_variants` | Every question has 1–3 legitimate variants |
| `human_readable_opening` | First paragraph is non-empty, has no personnel index, and <3 EMP tokens |
| `no_direct_token_transfer_reset` | Provenance stories never directly identify the tracked authorization token in a container-to-container transfer |

Current dataset assessor narration gates (intentionally stricter):

| Metric | Formula / threshold |
|--------|---------------------|
| Paragraphs | ≥5 |
| Word count | 500–2500, regex `\b[\w'-]+\b` |
| Sentence length | Nearest-rank P95 ≤45 words |
| Personnel index count | ≤1 |
| EMP token count | ≤6 |
| Direct token-transfer resets | 0 when `n<100`; ≤5% when `n≥100` |
| Dataset narration pass rate | 100% when `n<100`; ≥95% when `n≥100` |

The two identifier thresholds are not interchangeable: generation rejects severe failures;
dataset assessment applies the release-quality bar.

The direct-transfer gate prevents a provenance shortcut: a transfer may state that complete,
unexamined contents moved, but naming the tracked token in the destination would reset the state
chain and make earlier clues unnecessary. The formulaic detector also rejects the repeated v5
custody boilerplate “both initialed the same custody line” and “with both seams in view.”

### D. Dataset diversity

All formulas are implemented by `cogito_mill.eval.quality.assess_dataset`.

| Gate ID | Definition | Calibration (`n<100`) | Release-sized (`n≥100`) |
|---------|------------|------------------------|--------------------------|
| `no_exact_duplicates` | SHA-256 of normalized story text; `n - unique hashes` | 0 duplicates | 0 |
| `template_count` | Number of represented `template_id` values | ≥4 | ≥6 |
| `template_effective_count` | Inverse Simpson: `1 / Σ p_family²` | ≥3.5 | ≥5.0 |
| `template_max_share` | `max family count / n` | ≤0.34 | ≤0.20 |
| `setting_coverage` | Number of represented settings | ≥4 | ≥6 |
| `setting_entropy` | `-Σ p ln(p) / ln(k)` over represented settings | ≥0.75 | ≥0.85 |
| `surface_similarity_p95` | Nearest-rank P95 pairwise Jaccard over token 5-shingle sets | ≤0.65 | ≤0.65 |
| `unique_openings` | Unique normalized first-24-token openings / n | ≥0.80 | ≥0.80 |
| `question_stems` | Count of unique normalized main questions | ≥`min(8,n)` | ≥8 |
| `question_stem_max_share` | Largest normalized main-question share | ≤0.20 | ≤0.20 |
| `structural_hops` | Every declared `n_hops` | ≥10 | ≥10 |

`template_effective_count` and normalized setting entropy prevent nominal category coverage from
hiding a dominant family. Surface similarity is a warning against repeated prose, not semantic
proof of diversity.

### E. Difficulty and answer-form behavior

The canonical evaluator receives only story + reader-facing question and uses
`score_exact_any` after answer normalization.

| ID | Formula | Gate |
|----|---------|------|
| `eval.main_accuracy` | Correct main predictions / main predictions | Development hardness ≤0.30 |
| `eval.main_wilson_upper_95` | One-sided 95% Wilson upper bound, `z=1.645` | Release claim ≤0.30 |
| `eval.first_name_only_rate` | Incorrect bare-given-name predictions / eligible full-name questions | Diagnostic; target 0 and flag any regression |
| `eval.transport_errors` | Provider calls exhausted after retry | 0 |
| `eval.accuracy` | Correct predictions / all evaluated questions | Diagnostic; never substitute for main accuracy |

The Wilson bound is:

`(p + z²/(2n) + z*sqrt(p(1-p)/n + z²/(4n²))) / (1 + z²/n)`.

A small calibration pack may pass observed accuracy but fail the release claim. Report both.

### F. Batch efficiency and failure diagnostics

Always record these when generation behavior changes:

| ID | Formula | Status |
|----|---------|--------|
| `batch.acceptance_yield` | accepted / attempts | Diagnostic |
| `batch.rejection_rate` | rejected / attempts | Diagnostic |
| `batch.repair_rate` | accepted items requiring ≥1 repair / accepted | Diagnostic |
| `batch.attempts_per_accept` | attempts / accepted | Diagnostic |
| `batch.failure_reasons` | Counts by terminal reason / failed critic gate | Diagnostic |

No fixed thresholds are justified yet. Compare candidate against baseline and explain regressions;
do not optimize yield by weakening correctness gates.

### G. Human audit

Automated readability metrics do not establish narrative quality. For calibration and release
assessments, review a deterministic stratified sample:

- calibration (`n<100`): at least 6 items, one per family where possible;
- release-sized (`n≥100`): at least `max(10, ceil(0.10*n))`, capped at 30;
- select by sorted item ID within each family, not by convenience.

For each sampled item record pass/fail and a short finding for:

1. coherent story rather than disguised table;
2. clues naturally integrated and trackable;
3. no answer leak;
4. question unambiguous and answer form explicit;
5. local rules self-contained;
6. distractors plausible but not gratuitous.

Human audit is currently a required recorded diagnostic, not a replacement for deterministic
gates. A severe contradiction or answer leak blocks promotion and should become an automated
regression gate where feasible.

## Sample regimes and permissible claims

| Regime | Size / balance | Permissible claim |
|--------|----------------|-------------------|
| Smoke | 1–2 items | Code path executes; no diversity or quality claim |
| Development calibration | ≥12, balanced across all available families | Directional item/dataset quality and observed hardness |
| Release candidate | ≥100, all required families/settings represented | Apply release-sized pack gates |
| Statistical release | Release candidate plus Wilson upper bound ≤0.30 | Hardness claim against the recorded evaluator snapshot |

Passing one regime never implies a stronger regime.

## Changing this registry

A metric change requires:

1. rationale and expected failure mode;
2. old and new definitions;
3. backfill on the current baseline when computable;
4. protocol-version increment in the assessment record;
5. explicit note that pre/post values are not directly comparable when the formula changed.
