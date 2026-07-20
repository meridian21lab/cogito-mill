---
name: long-story-mvp
overview: Build one auditable, end-to-end “Long Story Short” pipeline that plans a formal mystery world, verifies it deterministically, renders a long story, derives a question bundle, critiques the result, and saves complete run provenance. The first milestone deliberately excludes batching, variants, publication, calibrated difficulty, probability, spatial/belief reasoning, and benchmark scoring.
todos:
  - id: lock-contract
    content: Record confirmed MVP decisions and replace the placeholder accepted-item schema
    status: pending
  - id: model-domain
    content: Add typed domain artifacts and LangGraph run state
    status: pending
  - id: build-solver
    content: Implement and fixture-test the Z3 relational/temporal compiler and causal simulator
    status: pending
  - id: build-agents
    content: Implement schema-constrained planner, formalizer, writer, critic, and renderer roles
    status: pending
  - id: assemble-graph
    content: Wire bounded repair gates, hierarchical generation, and full artifact provenance in LangGraph
    status: pending
  - id: verify-e2e
    content: Add CLI, offline tests, opt-in live smoke test, lint, and strict typing verification
    status: pending
isProject: false
---

# Long Story Short MVP

## Architecture
Use an explicit LangGraph `StateGraph`: typed state is the source of truth, LLM nodes produce schema-constrained artifacts, deterministic nodes enforce hard gates, and conditional edges implement at most two concept repairs before rejection.

```mermaid
flowchart LR
    Recipe[SampledRecipe] --> Concept[ConceptPlanner]
    Concept --> ConceptCritic[ConceptCritic]
    ConceptCritic -->|"revise max 2"| Concept
    ConceptCritic -->|accepted| Formalizer[WorldFormalizer]
    Formalizer --> WorldSolver[Z3AndCausalSolver]
    WorldSolver --> Evidence[EvidencePlanner]
    Evidence --> ProofCheck[VisibleTheoryProofCheck]
    ProofCheck --> Outline[OutlineAndCluePlacement]
    Outline --> Scenes[HierarchicalSceneWriter]
    Scenes --> StoryCritic[BlindStoryCritic]
    StoryCritic --> Questions[DeterministicTargetsAndQuestionRenderer]
    Questions --> FinalGate[FinalValidation]
    FinalGate --> Artifacts[VersionedRunArtifacts]
```

## 1. Lock the MVP contract in docs and schemas
- Keep the settled product contract in [`docs/vision.md`](docs/vision.md), the system design in [`docs/engineering/01-architecture.md`](docs/engineering/01-architecture.md), and the executable sequence in [`docs/engineering/02-agent-flow.md`](docs/engineering/02-agent-flow.md).
- Maintain stage invariants, hard gates, repair/rejection behavior, provider-per-run selection, visible-theory uniqueness, and deferred work in those three source-of-truth documents.
- Replace the placeholder [`schemas/reasoning-item.schema.json`](schemas/reasoning-item.schema.json) with the accepted-item projection: sentence-addressable story, canonical final answers, typed deduction steps, supporting conclusions, counterfactual, and minimal-falsifier tasks. Keep internal run artifacts as Pydantic schemas rather than forcing them into the release-item schema.

## 2. Establish typed domain and run-state modules
- Add Pydantic models under `src/cogito_mill/domain/` for `GenerationRecipe`, `ConceptBrief`, typed entities/relations, time points/intervals, events with preconditions/effects/inhibitors, complete `WorldSpec`, `VisibleTheory`, evidence/clue channels, atomic typed `DeductionStep`, story scenes/sentences, question bundles, critic reports, rejection reasons, and `RunManifest`.
- Encode invariants in the models where local; reserve cross-object consistency and entailment for the solver module.
- Add one small orchestration interface: a `MillState` carrying immutable/versioned stage artifacts, attempt counters, status, and validation reports. Avoid passing chat histories as pipeline state.

## 3. Build the deterministic reasoning module first
- Add `z3-solver` using `uv add z3-solver`; implement a deep module under `src/cogito_mill/reasoning/` that compiles relational, identity/cardinality, and temporal point/interval constraints to Z3 and simulates deterministic causal interventions.
- Expose a compact interface returning structured reports for: world satisfiability, target truth, visible-theory uniqueness across all consistent worlds, minimal supporting facts, canonical typed proof, material-strategy classification, counterfactual result, and minimal falsifying constraint set.
- Reject worlds that are inconsistent, underdetermined from disclosed facts, or admit a materially different reasoning strategy. Treat step reordering as equivalent.
- Develop against handwritten fixtures before any model calls so solver failures remain distinguishable from generation failures.

## 4. Implement schema-constrained agent roles
- Reuse [`src/cogito_mill/llm/providers.py`](src/cogito_mill/llm/providers.py) through `build_chat(provider, role=...)`; a run chooses Azure or GLM, and that family’s writer/judge deployments remain separate.
- Add focused agents/prompts under `src/cogito_mill/agents/`: recipe-driven concept planner, hard-gate concept critic, specialist world formalizer, evidence planner, outline/clue-placement planner, scene writer, blind story critic, trace verbalizer, and question renderer.
- Use structured model output into the domain schemas. Critics receive the rendered artifact and explicit rubric but not the generator’s free-form rationale.
- Keep deterministic responsibilities out of prompts: agents propose or render; code decides satisfiability, uniqueness, proof validity, counterfactual truth, and minimal falsification.

## 5. Assemble the explicit LangGraph and artifact store
- Implement the graph under `src/cogito_mill/pipelines/` with explicit nodes and conditional edges: concept repair is limited to two revisions; later failed stages receive bounded local repair feedback and then reject the run.
- Generate long prose hierarchically from an outline and shared fact ledger. Assign stable sentence IDs after assembly, then require evidence mappings and critic findings to reference those IDs.
- Derive question targets and gold answers from solver output before agent rendering. The final bundle starts with canonical final answers and includes supported conclusions, typed deduction steps, at least one causal counterfactual, and a minimal-falsifier task.
- Add a filesystem artifact adapter that writes an atomic run directory under `data/raw/`/`data/interim/`/`data/processed/`, containing stage JSON, prompt/model metadata, repairs, validation reports, rejection reasons, seeds, token/cost metadata when available, and a manifest. Never serialize credentials.

## 6. Expose and verify one end-to-end run
- Extend [`src/cogito_mill/cli.py`](src/cogito_mill/cli.py) with a single-item command accepting provider, seed, and output root; preserve the existing provider configuration in [`src/cogito_mill/config/settings.py`](src/cogito_mill/config/settings.py).
- Add unit tests for every schema invariant, Z3 compilation rule, causal intervention, uniqueness proof, minimal support/falsifier extraction, sentence-ID mapping, and atomic artifact writes.
- Add integration tests for graph routing and repair exhaustion using fake structured-output model adapters; test both provider selections without network calls.
- Replace the skipped E2E placeholder with: an offline deterministic fixture test that always runs, plus an opt-in live one-item smoke test requiring configured secrets.
- Verify with `uv run pytest tests/unit -q`, `uv run pytest tests/integration -q`, `uv run ruff check src tests`, and `uv run mypy`; run the live E2E only after offline checks pass.

## Deferred after the first accepted item
- Same-logic rerenders and logic-changing world variants; 100–200-world pilot batching.
- Structural/empirical difficulty calibration, ordinal likelihood, spatial and belief models.
- Multi-provider review within one run, demographic audits, Hugging Face packaging/publishing, gated distribution, and benchmark scoring.