# Long Story Short — product and data vision

Status: **accepted for MVP implementation**.

## Purpose

Long Story Short is a fully synthetic dataset of long narrative deduction problems. Its
eventual purpose is to train and evaluate MrCogito-style concept-forming reasoners on
evidence-grounded understanding rather than familiar-riddle recall or fluent
post-hoc explanation.

The stories use detective fiction, domestic situations, workplaces, expeditions,
historical settings, and explicitly defined speculative worlds. A model must reconstruct
relationships, time, and deterministic causal chains from dispersed evidence; derive a
unique answer; explain the successful deduction; answer counterfactual questions; and
identify minimal evidence that falsifies a supplied hypothesis.

## Measurement thesis

Final-answer accuracy alone cannot distinguish reasoning from substitution heuristics.
Long Story Short therefore separates:

1. **Latent logic from narrative surface.** Every item begins as a typed, machine-checkable
   world and is rendered into prose only after the world is validated.
2. **The complete world from disclosed evidence.** A unique actual answer is insufficient.
   Exactly one answer must follow in every world consistent with the facts shown to the
   reader.
3. **Outcome from process evidence.** The answer is scored independently, while an ordered
   structured trace exposes evidence selection and inference dependencies.
4. **Causation from temporal coincidence.** Deterministic interventions recompute downstream
   state and produce counterfactual questions.
5. **Logical status from plausibility.** MVP questions use entailed, contradicted, possible,
   and impossible. Subjective ordinal probability is deferred until its semantics can be
   defined.

The later benchmark will add two controlled variant axes:

- same logic, different surface, where conclusions must remain invariant;
- nearly identical surface, changed logic, where conclusions must update.

Variants are deliberately deferred from the first executable milestone.

## Evidence-informed positioning

The design occupies a practical gap between short synthetic mysteries and full novels:

- [MuSR](https://arxiv.org/abs/2310.16049) demonstrates symbolic-structure-to-narrative
  generation, but its stories are much shorter than the intended distribution.
- [DetectiveQA](https://arxiv.org/abs/2409.02465) anchors reasoning steps to evidence in
  novel-length contexts, but uses copyrighted source narratives and contexts far beyond the
  initial target.
- [Premise Order Matters](https://proceedings.mlr.press/v235/chen24i.html),
  [Shortcut Suite](https://aclanthology.org/2024.emnlp-main.679/), and
  [GSM-DC](https://aclanthology.org/2025.emnlp-main.674/) motivate controlled ordering,
  distractor, and surface perturbations.
- [BRAINTEASER](https://aclanthology.org/2023.emnlp-main.885/) motivates reconstructed
  lateral-thinking variants but also illustrates contamination risk from web-circulated
  riddles.
- [PRM800K](https://arxiv.org/abs/2305.20050) motivates step-level supervision, while
  chain-of-thought faithfulness research cautions that fluent free-form rationales are not
  proof of the model's actual computation.

These precedents inform the design; they are not data sources. MVP stories are original and
fully synthetic.

## Settled data contract

### World and reasoning scope

- Every item has a hidden typed world model.
- MVP composes three reasoning families:
  - typed relational identity and constraints;
  - temporal points, intervals, order, overlap, and duration;
  - deterministic causal events with preconditions, effects, and inhibitors.
- The story is self-contained. No deduction-critical external knowledge is permitted.
- Local rules may differ from ordinary reality only when the story states them explicitly.
- Characters' beliefs, nested knowledge, lies as epistemic state, and theory of mind are
  outside MVP. Statements may occur as events, but objective world truth is authoritative.
- Every scored question has one uniquely entailed answer from visible evidence.
- The intended solution must not admit a materially different reasoning strategy. Harmless
  reordering of equivalent steps is allowed.

### Narrative

- English only for MVP; the latent world remains language-neutral.
- Natural and engaging, but clarity takes priority over literary ambiguity.
- Context length is an outcome of world complexity, not a hard construction quota.
- The eventual distribution should lean toward approximately 16K-token stories. Valid
  stories may range from roughly 4K to 32K or longer when their evidence structure warrants
  it; padding is prohibited.
- Settings are diverse and should later support matched logic across narrative skins.
- Prose may use natural names, aliases, roles, and pronouns; hidden stable entity IDs preserve
  machine identity.
- Critical clues use typed channels: direct statement, observation, record, physical state,
  or explicit rule application.
- Distractors mix irrelevant facts, plausible red herrings, and graph-connected facts that
  are irrelevant to the current question.
- Provider policies are the minimum content restriction during the pilot. Release suitability
  is a separate future gate.

### Questions and answers

Each world produces a question bundle. The response contract puts an easy-to-validate
canonical final answer first, followed by supported conclusions and ordered deduction steps.
The bundle contains:

- the main uniquely answerable mystery;
- intermediate supported conclusions;
- at least one deterministic causal counterfactual;
- a supplied false hypothesis requiring a minimal falsifying evidence/constraint set.

Every narrative sentence receives a stable ID. Each atomic deduction step contains:

- source sentence IDs and/or prior-step IDs;
- a controlled inference type;
- a canonical conclusion;
- an optional concise natural-language explanation.

The gold trace records only the successful path. It is derived by the solver from visible
facts and then verbalized by an agent; it is never accepted merely because a model wrote a
convincing explanation.

## MVP goal

The first executable milestone produces **one complete, inspectable item**:

`recipe → concept → critique → formal world → deterministic proof → evidence plan → long
story → story critique → question bundle → final validation → versioned artifacts`

The MVP exists to refine the agentic generation and verification pipeline. It is not yet a
public benchmark, training corpus, leaderboard, or Hugging Face release.

## MVP success criteria

The milestone is successful when:

1. one item reaches `accepted` through the real graph;
2. every LLM output conforms to a versioned schema;
3. Z3 and the causal simulator prove consistency, visible-evidence uniqueness,
   counterfactual truth, the canonical proof, and minimal falsification;
4. the story critic finds no missing, contradictory, leaked, or ambiguous critical facts;
5. all stages, repairs, model/deployment metadata, seeds, and validation reports are retained;
6. deterministic tests run without provider credentials;
7. an opt-in cloud run can use either the Azure or GLM model family.

## Explicitly deferred

- generating 100–200 pilot worlds and later 10K+ documents;
- training MrCogito or any other model;
- controlled variant families;
- spatial and epistemic/theory-of-mind reasoning;
- ordinal probability and calibration;
- empirical difficulty labels and acceptance thresholds;
- demographic distribution analysis;
- Hugging Face packaging, licensing, gated access, and publication;
- benchmark scoring, submission infrastructure, and leaderboards;
- serving inference APIs.
