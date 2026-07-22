# Long Story Short — agent flow and implementation plan

Status: **accepted MVP plan**.

This document is the executable sequence for the architecture in `01-architecture.md`. It
combines the agent flow, deterministic gates, delivery phases, and post-MVP roadmap.

## Delivery strategy

Implement one vertical slice end to end before adding scale or capability breadth. The first
accepted item is the integration target. Each phase leaves deterministic tests and a usable
interface; model calls are introduced only after the formal core works against fixtures.

## Phase 0 — Contract and fixtures

### Changes

1. Replace `schemas/reasoning-item.schema.json` with the accepted-item projection:
   - item/run/schema version IDs;
   - sentence-addressable story;
   - question bundle;
   - canonical final answers;
   - supported conclusions;
   - typed successful deduction steps;
   - counterfactual intervention/answer;
   - minimal falsifier;
   - provenance safe for release.
2. Add Pydantic internal artifact schemas under `src/cogito_mill/domain/`.
3. Write one small handwritten relational–temporal–causal fixture with:
   - a complete world;
   - a visible theory;
   - a uniquely entailed answer;
   - one causal counterfactual;
   - one false hypothesis and minimal falsifier;
   - at least one distractor.

### Exit criteria

- JSON schema and Pydantic accepted-item serialization agree.
- Invalid references, duplicate IDs, malformed intervals, and incomplete typed steps fail
  locally.
- The fixture expresses all MVP output types without using an LLM.

## Phase 1 — Deterministic reasoning core

### Dependency

Add Z3 through the project package manager:

```bash
uv add z3-solver
```

Commit both `pyproject.toml` and `uv.lock`.

### Implementation order

1. Compile entity identity/inequality and typed relations.
2. Add inverse, symmetry, exclusivity, cardinality, and declared transitivity constraints.
3. Compile time points and intervals, relative order, overlap, and durations.
4. Implement deterministic event execution:
   - check preconditions;
   - apply inhibitors;
   - apply effects;
   - preserve causal-parent provenance.
5. Implement interventions by replacing/removing the selected event or fact and recomputing
   affected downstream state.
6. Prove the target in the complete world.
7. Prove visible-theory uniqueness by searching for a satisfying model with a different
   answer.
8. Minimize the required support facts.
9. Build the canonical typed proof and minimal falsifier.
10. Detect materially different reasoning strategies conservatively.

### Required reports

- `WorldAnalysis`: satisfiable, violations, derived facts, target truth, causal trace.
- `DisclosureAnalysis`: answerable, unique, alternative model if not unique, minimal support,
  canonical proof, strategy classification.
- `CounterfactualAnalysis`: intervention, recomputed changes, target answer.
- `FalsificationAnalysis`: hypothesis, status, minimal contradictory set.

### Exit criteria

- All reports are deterministic and serializable.
- Unsatisfiable worlds provide actionable errors to a formalizer.
- A hidden-world answer that is not unique from visible evidence is rejected.
- Counterfactual results change only through declared causal descendants.
- Unit tests cover positive, negative, boundary, and minimization cases.

## Phase 2 — Model interface and agent roles

### Model seam

Add an injectable structured-output interface over the existing `build_chat()` factories.
Production adapters use LangChain structured output. Tests use deterministic fakes keyed by
role and attempt.

Every call records:

- provider family and deployment/model;
- mill role (`writer` or `judge`);
- agent role;
- prompt and output-schema versions;
- request attempt and latency;
- token/cost metadata when the provider returns it;
- parse/transport/content failure category.

Credentials and full settings are never recorded.

### Agents

Implement in this order:

1. **Concept planner**
   - receives one sampled recipe;
   - returns one compact premise, intended target, and expected composition;
   - may revise from structured critic feedback.
2. **Concept critic**
   - independently gates formalizability, unique-answer potential, self-containment,
     relational–temporal–causal necessity, variantability, and shortcut risk;
   - returns accept/revise/reject plus one finding per failed gate.
3. **World formalizer**
   - turns an accepted concept into `WorldSpec`;
   - has no prose-writing responsibility.
4. **Evidence planner**
   - receives the solver's minimal support;
   - creates a visible theory and controlled distractors.
5. **Outline planner**
   - distributes required clues and narrative events across scenes;
   - preserves reveal order and the shared fact ledger.
6. **Scene writer**
   - renders one scene at a time against explicit obligations;
   - cannot invent or alter formal facts.
7. **Story critic**
   - reads the assembled story and grounding contract, not generator rationale;
   - reports omissions, contradictions, answer leaks, ambiguity, invalid implication,
     awkward clue realization, and ungrounded additions.
8. **Trace verbalizer**
   - adds concise explanations to solver-generated typed steps;
   - cannot change premises, inference type, or conclusion.
9. **Question renderer**
   - phrases solver-derived tasks and canonical answers;
   - cannot invent target semantics.
10. **Final critic**
    - checks the complete item for consistency and usability;
    - disagreement with deterministic gold quarantines the item.

### Exit criteria

- Every agent result parses directly into its output schema.
- Invalid structured output is a content failure with bounded repair, not accepted text.
- Writer and judge roles use different deployments/models inside the selected family.
- Tests run both Azure and GLM routing through fakes without network access.

## Phase 3 — Planning and disclosure graph

### Recipe sampling

MVP may begin with one checked-in recipe fixture. The recipe still records:

- all three required reasoning families;
- setting and narrative constraints;
- clue/distractor obligations;
- required question types;
- requested difficulty metadata;
- seed and version IDs;
- prohibited shortcuts.

Difficulty is not an acceptance gate in this phase.

### Concept loop

```text
concept planner → concept critic
      ↑                │
      └── revise ──────┘  at most two revisions
```

After two failed revisions, terminate as `rejected`. Preserve every proposal and critique.

### Formalization and solving

1. Formalizer creates the complete world and target.
2. Pydantic validates local shape.
3. Solver validates global consistency and target truth.
4. Structured errors permit bounded stage-local repair.
5. Persistent failure rejects the run.

### Disclosure construction

1. Solver returns a minimal sufficient support set.
2. Evidence planner assigns typed clue channels and narrative placement.
3. Planner adds controlled distractors.
4. Solver checks visible-theory uniqueness after enrichment.
5. Solver extracts canonical proof, counterfactual, and falsifier from the visible theory.

### Exit criteria

- A graph run can reach a fully validated disclosure without prose.
- Repair counters and terminal reasons are correct and persisted.
- No agent self-certifies satisfiability or uniqueness.

## Phase 4 — Hierarchical narrative generation

### Outline

The outline defines scenes, viewpoint/style constraints, event order, scene-level participants,
fact-ledger obligations, clue channels, and distractor placement. It does not target a fixed
token count. Story length emerges from the number and dispersion of required events and facts.

### Scene generation

Generate scenes separately to avoid context drift. Each scene receives:

- immutable relevant world facts;
- facts already revealed;
- facts that must be revealed in this scene;
- facts that must remain hidden;
- local continuity summary;
- style policy;
- stable entity/alias registry.

### Assembly

1. Join scenes in outline order.
2. Normalize paragraph and sentence segmentation.
3. Assign stable sentence IDs.
4. Map every visible fact to one or more sentence IDs.
5. Reject unmapped required facts and unregistered formal claims.
6. Run the blind story critic.
7. Apply bounded scene-local repairs where possible; invalidate later mappings after edits.

### Grounding gates

- Every required visible fact is faithfully rendered.
- No story claim contradicts the complete world.
- No hidden answer fact leaks before its intended derivation.
- Natural aliases resolve to one hidden entity.
- Critical clues remain unambiguous and self-contained.
- Distractors do not create another valid answer or materially different solution strategy.
- Explicit local rules appear before they are required.

### Exit criteria

- A validated assembled story has complete fact-to-sentence mapping.
- Critic findings reference sentence IDs and formal fact IDs.
- Repairing one scene causes deterministic remapping and revalidation.

## Phase 5 — Question bundle and final acceptance

### Deterministic derivation

Code derives task targets before natural-language rendering:

- main mystery claim and answer;
- selected supported intermediate conclusions;
- at least one intervention and its counterfactual result;
- one false hypothesis and minimal falsifying set;
- canonical typed successful proof.

### Rendering

The question renderer receives only these targets and the sentence-addressable story. The
accepted response projection orders fields as:

1. canonical final answer;
2. supported conclusions;
3. ordered typed deduction steps with evidence sentence IDs;
4. counterfactual answer and support;
5. minimal falsifier.

### Final gate

Acceptance requires:

- all artifact schemas valid;
- deterministic world and disclosure checks passing;
- all gold evidence IDs present in the final story;
- question semantics matching solver targets;
- critic passing grounding and usability checks;
- no unresolved critic/solver disagreement;
- complete provenance manifest.

Disagreement produces `quarantined`; it never resolves by majority vote or by trusting the
symbolic world alone.

## Phase 6 — Artifact persistence and CLI

### Artifact transitions

- `data/raw/<run_id>`: recipe, prompts, all model attempts, failures, and manifest.
- `data/interim/<run_id>`: latest validated formal and narrative artifacts.
- `data/processed/<run_id>`: accepted `reasoning-item.json` and acceptance report.

Each stage write is atomic. The manifest contains content hashes and parent-version links so a
resumed run can detect stale downstream artifacts. Resume/idempotency beyond one local run may
be added after the first accepted item, but the schema must not preclude it.

### CLI

Initial interface:

```bash
uv run cogito-mill generate-one \
  --provider azure \
  --seed 42 \
  --output-root data
```

`--provider glm` selects the GLM family. The command prints the run ID, terminal status,
artifact directory, and concise rejection/quarantine summary. It does not publish.

### Exit criteria

- Interrupted writes do not create a processed item.
- Re-running tests never requires `.env`.
- A cloud agent with configured secrets can execute one live run.

## Phase 7 — Verification and cloud handoff

### Default checks

```bash
uv sync --frozen --all-groups
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run ruff check src tests
uv run mypy
```

### E2E tiers

1. Offline fixture E2E: handwritten world plus fake agents, always run.
2. Live Azure E2E: opt-in and secret-gated.
3. Live GLM E2E: opt-in and secret-gated.

The live test generates one item and may terminate accepted, rejected, or quarantined. A
provider call succeeding is not sufficient: the run must preserve a complete diagnosable
artifact history.

## Implementation sequence

1. Domain schemas and handwritten fixture.
2. Z3 compiler and causal simulator.
3. Proof, uniqueness, counterfactual, and falsifier extraction.
4. Filesystem artifact adapter and manifests.
5. Injectable structured model interface.
6. Concept/formalizer/evidence agents.
7. Planning and disclosure LangGraph.
8. Outline/scene generation and story grounding.
9. Question rendering and final gate.
10. CLI and offline E2E.
11. One live cloud run with one selected provider family.
12. Inspect artifacts and revise schemas/prompts before any batching.

## Phase 8 — Pilot batch, Hub publish, Luna eval (authorized)

### Goals

- Batch-generate 100–200 accepted items with template-backed recipes.
- Pack a thin Hub projection and publish `ksopyla/long-story-short-pilot`.
- Blind-evaluate Azure Luna (writer deployment) on story+question only.
- If accuracy > 30%, identify the measured failure mode, tighten structural difficulty, and
  repeat. Narration and diversity must pass before each Luna run.

### CLI

```bash
uv run cogito-mill generate-batch --provider azure --n 200
uv run cogito-mill publish --repo ksopyla/long-story-short-pilot --config pilot_v0
uv run cogito-mill evaluate --dataset ksopyla/long-story-short-pilot --solver-provider azure
```

### Exit criteria

- ≥100 accepted locally verified items (target 150–200).
- Local pack always works; Hub publish requires a write-capable `HF_TOKEN`.
- Eval metrics JSON retained under `data/processed/evals/`.
- Development gate: observed Luna main-question accuracy ≤30% with full prediction coverage.
- Release gate: one-sided 95% Wilson upper bound ≤30% on a larger balanced pack.
- Narration and pack-level diversity gates pass independently; hardness never compensates for
  unreadable or repeated stories.

## Post-MVP roadmap

After the pilot slice stabilizes:

1. add same-world rerenders;
2. add world-transform logic variants;
3. calibrate structural difficulty metrics beyond the Luna gate;
4. add spatial and later epistemic reasoning;
5. define ordinal probability semantics;
6. design benchmark scoring and gated distribution;
7. scale toward 10K+ documents and audit representation.
