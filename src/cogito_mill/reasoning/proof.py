"""Canonical proof and falsifier extraction."""

from __future__ import annotations

from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.reasoning import DeductionStep, InferenceType
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning.causal import simulate


def build_canonical_proof(
    world: WorldSpec,
    visible: VisibleTheory,
    answer: str,
) -> list[DeductionStep]:
    facts, trace = simulate(world)
    steps: list[DeductionStep] = []
    required = [f for f in visible.facts if f.role == "required"]
    for idx, fact in enumerate(required, start=1):
        steps.append(
            DeductionStep(
                id=f"s{idx}",
                evidence_fact_ids=[fact.id],
                inference_type=InferenceType.LOOKUP,
                conclusion=fact.text,
                explanation=f"Observe disclosed fact {fact.id}.",
            )
        )
    # elimination summary
    eliminated = [
        f.formal.split(":", 1)[1] for f in visible.facts if f.formal.startswith("eliminated:")
    ]
    if eliminated:
        steps.append(
            DeductionStep(
                id=f"s{len(steps) + 1}",
                evidence_fact_ids=[
                    f.id for f in visible.facts if f.formal.startswith("eliminated:")
                ],
                prior_step_ids=[steps[-1].id] if steps else [],
                inference_type=InferenceType.ELIMINATION,
                conclusion=f"Eliminate candidates: {', '.join(eliminated)}",
                explanation="Visible constraints rule out these candidates.",
            )
        )
    if trace:
        steps.append(
            DeductionStep(
                id=f"s{len(steps) + 1}",
                prior_step_ids=[steps[-1].id] if steps else [],
                inference_type=InferenceType.CAUSAL_EFFECT,
                conclusion=f"Causal trace: {' -> '.join(trace)}",
                explanation="Deterministic events fire in time order under preconditions.",
            )
        )
    label = next(e.label for e in world.entities if e.id == answer)
    steps.append(
        DeductionStep(
            id=f"s{len(steps) + 1}",
            prior_step_ids=[steps[-1].id] if steps else [],
            inference_type=InferenceType.CONCLUSION,
            conclusion=label,
            explanation=(
                f"Unique surviving answer is {label} ({answer}). "
                f"Derived facts include {sorted(facts)[:8]}."
            ),
        )
    )
    return steps


def minimal_support(visible: VisibleTheory) -> list[str]:
    return [f.id for f in visible.facts if f.role == "required"]


def minimal_falsifier(
    world: WorldSpec,
    visible: VisibleTheory,
    false_hypothesis: str,
) -> list[str]:
    """Return a small set of visible fact IDs that contradict the hypothesis."""
    contradicting: list[str] = []
    for fact in visible.facts:
        if fact.formal == f"eliminated:{false_hypothesis}":
            contradicting.append(fact.id)
        if (
            fact.formal.startswith("actor_must_be:")
            and fact.formal != f"actor_must_be:{false_hypothesis}"
        ):
            contradicting.append(fact.id)
        if fact.formal.startswith("absent:") and fact.formal.startswith(
            f"absent:{false_hypothesis}:"
        ):
            contradicting.append(fact.id)
    if not contradicting:
        # fallback: any required fact naming a different actor
        for fact in visible.facts:
            if world.answer_entity in fact.formal and false_hypothesis not in fact.formal:
                contradicting.append(fact.id)
                break
    return contradicting[:3]
