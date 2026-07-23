"""Canonical proof and falsifier extraction."""

from __future__ import annotations

from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.logic import LogicAtom
from cogito_mill.domain.reasoning import DeductionStep, InferenceType
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning.causal import simulate
from cogito_mill.reasoning.logic import derive, proof_keys


def build_canonical_proof(
    world: WorldSpec,
    visible: VisibleTheory,
    answer: str,
) -> list[DeductionStep]:
    if visible.constraints is not None:
        return _build_constraint_proof(world, visible, answer)
    if visible.logic is not None:
        return _build_logic_proof(visible, answer)

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
    if visible.logic is not None:
        # The support is the visible realization of the proof, including local rules.
        return [fact.id for fact in visible.facts if fact.role == "required"]
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


def _build_logic_proof(visible: VisibleTheory, answer: str) -> list[DeductionStep]:
    assert visible.logic is not None
    theory = visible.logic
    goal = LogicAtom(predicate=theory.goal_predicate, arguments=[answer])
    closure = derive(theory)
    keys = proof_keys(theory, goal)
    fact_id_by_formal = {fact.formal: fact.id for fact in visible.facts}
    step_id_by_key: dict[str, str] = {}
    rules = {rule.id: rule for rule in theory.rules}
    steps: list[DeductionStep] = []

    for key in keys:
        derivation = closure[key]
        step_id = f"s{len(steps) + 1}"
        step_id_by_key[key] = step_id
        if derivation.rule_id is None:
            evidence = fact_id_by_formal.get(f"atom:{key}")
            steps.append(
                DeductionStep(
                    id=step_id,
                    evidence_fact_ids=[evidence] if evidence else [],
                    inference_type=InferenceType.LOOKUP,
                    conclusion=key,
                    explanation="Observe a disclosed premise.",
                )
            )
            continue

        rule = rules[derivation.rule_id]
        evidence = fact_id_by_formal.get(f"rule:{rule.id}")
        rule_id = rule.id.lower()
        inference = (
            InferenceType.RELATION_COMPOSE
            if "relation" in rule_id
            else InferenceType.TEMPORAL_ORDER
            if "temporal" in rule_id
            else InferenceType.CAUSAL_EFFECT
            if "causal" in rule_id
            else InferenceType.CONCLUSION
        )
        steps.append(
            DeductionStep(
                id=step_id,
                evidence_fact_ids=[evidence] if evidence else [],
                prior_step_ids=[
                    step_id_by_key[p] for p in derivation.premise_keys if p in step_id_by_key
                ],
                inference_type=inference,
                conclusion=key,
                explanation=rule.explanation,
            )
        )
    return steps


def _build_constraint_proof(
    world: WorldSpec,
    visible: VisibleTheory,
    answer: str,
) -> list[DeductionStep]:
    assert visible.constraints is not None
    steps: list[DeductionStep] = []
    for clue in visible.constraints.clues:
        inference = (
            InferenceType.TEMPORAL_ORDER
            if "before" in clue.kind or "time" in clue.axes
            else InferenceType.RELATION_COMPOSE
        )
        steps.append(
            DeductionStep(
                id=f"s{len(steps) + 1}",
                evidence_fact_ids=[clue.id],
                inference_type=inference,
                conclusion=clue.text,
                explanation=f"Apply visible relational constraint {clue.id}.",
            )
        )
    label = next(entity.label for entity in world.entities if entity.id == answer)
    steps.append(
        DeductionStep(
            id=f"s{len(steps) + 1}",
            prior_step_ids=[step.id for step in steps],
            inference_type=InferenceType.CONCLUSION,
            conclusion=label,
            explanation=(
                f"Z3 finds {label} as the only possible owner of "
                f"{visible.constraints.target_object}."
            ),
        )
    )
    return steps
