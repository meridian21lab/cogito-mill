"""Diverse, solver-checked concept-induction puzzle portfolio."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cogito_mill.domain.evidence import ClueChannel, VisibleFact, VisibleTheory
from cogito_mill.domain.logic import LogicAtom, LogicRule, LogicTheory
from cogito_mill.domain.narrative import SceneDraft, StoryDraft
from cogito_mill.domain.questions import (
    CounterfactualTask,
    FalsifierTask,
    QuestionBundle,
    ScoredQuestion,
)
from cogito_mill.domain.recipe import GenerationRecipe
from cogito_mill.domain.world import (
    Entity,
    Event,
    Intervention,
    TargetClaim,
    TimePoint,
    WorldSpec,
)
from cogito_mill.eval.score import name_answer_variants
from cogito_mill.pipelines.templates import FIRST, LAST

BRANCHES = (
    "relation",
    "temporal",
    "causal",
    "spatial",
    "sequence",
    "protocol",
)
STATUS_BANK = ("clear", "dormant", "latent", "open", "stable", "waking")


@dataclass(frozen=True)
class FamilySpec:
    id: str
    concept: str
    setting: str
    incident: str
    branch_nouns: tuple[str, ...]


FAMILIES = (
    FamilySpec(
        "watch_handover",
        "concordant watchkeeper",
        "an icebound research vessel changing watches during a storm",
        "the emergency ballast release",
        (
            "mentor pennant",
            "watch interval",
            "alarm consequence",
            "assigned station",
            "handover order",
            "seal notch",
        ),
    ),
    FamilySpec(
        "archive_provenance",
        "true chain custodian",
        "a monastic archive moving manuscripts before a flood",
        "the protected folio's final transfer",
        (
            "copying lineage",
            "bell interval",
            "wax reaction",
            "archive room",
            "transfer order",
            "cord pattern",
        ),
    ),
    FamilySpec(
        "fault_network",
        "convergent responder",
        "an orbital habitat tracing a cascading cooling fault",
        "the isolation command that restored the habitat",
        (
            "relay affiliation",
            "diagnostic interval",
            "downstream symptom",
            "service sector",
            "response order",
            "breaker mark",
        ),
    ),
    FamilySpec(
        "delegated_authority",
        "valid emergency delegate",
        "a city museum evacuating its collection during a power failure",
        "the lawful release of the sealed collection",
        (
            "deputy chain",
            "authority window",
            "release consequence",
            "collection zone",
            "signature order",
            "witness token",
        ),
    ),
    FamilySpec(
        "expedition_signal",
        "coherent signal bearer",
        "a desert expedition decoding a chain of emergency beacons",
        "the transmission that redirected the rescue convoy",
        (
            "team pairing",
            "signal interval",
            "repeater response",
            "beacon sector",
            "relay order",
            "cipher glyph",
        ),
    ),
    FamilySpec(
        "workshop_provenance",
        "certified restoration lead",
        "a conservation workshop tracing a damaged artifact through several rooms",
        "the treatment that stabilized the artifact",
        (
            "apprentice lineage",
            "work interval",
            "chemical response",
            "workshop room",
            "treatment order",
            "tool stamp",
        ),
    ),
)

MAIN_STEMS = (
    "Under the local rules, who alone became the {concept}? Give the full name.",
    "Which participant satisfies every condition for {concept}? Answer with the full name.",
    "Reconstruct the six evidence streams. Who qualifies as {concept}? Provide the full name.",
    "Whose combined record makes that person the {concept}? Give the full name.",
    "After applying all stated rules, identify the {concept} by full name.",
    "Who is forced to be the {concept}, rather than merely matching part of the pattern? "
    "Give the full name.",
    "Which full name belongs to the only person who meets the definition of {concept}?",
    "Resolve the local concept from the evidence: who is the {concept}? Give the full name.",
)


@dataclass
class ConceptPuzzle:
    family_id: str
    world: WorldSpec
    visible: VisibleTheory
    questions: QuestionBundle
    offline_draft: StoryDraft
    n_hops: int


def build_concept_puzzle(recipe: GenerationRecipe) -> ConceptPuzzle:
    """Build one portfolio member with a unique Horn-theory answer."""
    family = FAMILIES[(recipe.seed // len(FAMILIES)) % len(FAMILIES)]
    names = _names(recipe.seed, recipe.n_suspects)
    answer_idx = _pick(recipe.seed, "answer", len(names))
    runner_idx = (answer_idx + 1 + _pick(recipe.seed, "runner", len(names) - 1)) % len(names)
    if runner_idx == answer_idx:
        runner_idx = (runner_idx + 1) % len(names)
    answer_id, answer_label = names[answer_idx]
    runner_id, runner_label = names[runner_idx]

    assignments = _assignments(recipe.seed, names, answer_idx, runner_idx)
    status_by_person: dict[str, dict[str, str]] = {person_id: {} for person_id, _label in names}
    logic_facts: list[LogicAtom] = [LogicAtom(predicate="protocol_active")]
    rules: list[LogicRule] = []
    visible_facts: list[VisibleFact] = [
        _visible(
            "f_protocol_active",
            (
                f"For this incident, the board declared the {family.concept} protocol active; "
                "ordinary rank and reputation did not count."
            ),
            LogicAtom(predicate="protocol_active"),
            "sc1",
            1,
        )
    ]
    order = 2
    for branch_idx, branch in enumerate(BRANCHES):
        noun = family.branch_nouns[branch_idx]
        for person_id, _label in names:
            status_by_person[person_id][branch] = assignments[branch][person_id]

        for person_idx, (person_id, label) in enumerate(names):
            status = assignments[branch][person_id]
            atom = LogicAtom(
                predicate="derived_status",
                arguments=[branch, person_id, status],
            )
            logic_facts.append(atom)
            visible_facts.append(
                _visible(
                    f"f_{branch}_{person_id}",
                    _assignment_sentence(
                        family,
                        branch,
                        noun,
                        label,
                        status,
                        person_idx,
                    ),
                    atom,
                    f"sc{2 + (branch_idx + person_idx) % 3}",
                    order,
                )
            )
            order += 1

    weights, coefficients, start_value, modulus, checksums = _checksum_plan(
        recipe.seed,
        status_by_person,
        answer_id=answer_id,
        runner_id=runner_id,
    )
    for status, weight in weights.items():
        atom = LogicAtom(predicate="status_weight", arguments=[status, str(weight)])
        logic_facts.append(atom)
        visible_facts.append(
            _visible(
                f"f_weight_{status}",
                f"The checksum ledger assigned {status} status a value of {weight}.",
                atom,
                "sc1",
                order,
            )
        )
        order += 1
    formula_fact = VisibleFact(
        id="f_checksum_formula",
        text=(
            f"The checksum began at {start_value}. In order it used relation, temporal, "
            "causal, spatial, sequence, and protocol statuses with coefficients "
            f"{', '.join(str(c) for c in coefficients)}. At each stream, the panel squared "
            "the current checksum, added that stream's coefficient times its status value, "
            f"and kept the remainder modulo {modulus}. It made three passes: first in the "
            "stated order, then in reverse order with the coefficients reversed, then once "
            "more in the stated order with the coefficient list rotated one place left."
        ),
        formal="rule:checksum_formula",
        channel=ClueChannel.RULE_APPLICATION,
        role="required",
        scene_id="sc1",
        reveal_order=order,
    )
    visible_facts.append(formula_fact)
    order += 1

    for person_id, _label in names:
        checksum_rule = LogicRule(
            id=f"checksum_{person_id}",
            premises=[
                LogicAtom(
                    predicate="derived_status",
                    arguments=[branch, person_id, status_by_person[person_id][branch]],
                )
                for branch in BRANCHES
            ],
            conclusion=LogicAtom(
                predicate="checksum",
                arguments=[person_id, str(checksums[person_id])],
            ),
            explanation=(f"Apply the disclosed iterated modulo-{modulus} checksum to {person_id}."),
        )
        rules.append(checksum_rule)

    checksum_key = LogicAtom(
        predicate="checksum_key",
        arguments=[str(checksums[answer_id])],
    )
    logic_facts.append(checksum_key)
    visible_facts.append(
        _visible(
            "f_checksum_key",
            (f"For this incident, the accepted checksum was {checksums[answer_id]}."),
            checksum_key,
            "sc5",
            order,
        )
    )
    order += 1
    final_rule = LogicRule(
        id=f"final_{family.id}",
        premises=[
            LogicAtom(
                predicate="checksum",
                arguments=["?person", "?value"],
            ),
            LogicAtom(predicate="checksum_key", arguments=["?value"]),
            LogicAtom(predicate="protocol_active"),
        ],
        conclusion=LogicAtom(predicate="qualifies", arguments=["?person"]),
        explanation=(
            f"The title {family.concept} belongs to the person whose checksum matches the key."
        ),
    )
    rules.append(final_rule)
    visible_facts.append(
        _rule_visible(
            final_rule,
            (
                f"The final definition was strict: the {family.concept} was the one person "
                "whose six-stream checksum equaled the accepted checksum."
            ),
            "sc5",
            order,
        )
    )

    visible = VisibleTheory(
        id=f"vis-{recipe.seed}",
        world_id=f"world-{recipe.seed}",
        facts=visible_facts,
        logic=LogicTheory(facts=logic_facts, rules=rules),
    )
    world = _world(recipe, names, answer_id, family)
    questions = _questions(
        recipe,
        family,
        answer_label,
        runner_label,
        str(checksums[answer_id]),
        str(checksums[runner_id]),
        runner_id,
    )
    draft = _offline_draft(recipe, family, visible_facts)
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=visible,
        questions=questions,
        offline_draft=draft,
        n_hops=22,
    )


def _names(seed: int, n: int) -> list[tuple[str, str]]:
    names: list[tuple[str, str]] = []
    for i in range(n):
        digest = hashlib.sha256(f"{seed}:concept-name:{i}".encode()).digest()
        label = f"{FIRST[digest[0] % len(FIRST)]} {LAST[digest[1] % len(LAST)]}"
        suffix = 2
        while any(existing == label for _, existing in names):
            label = f"{label.split('-')[0]}-{suffix}"
            suffix += 1
        names.append((f"p{i}", label))
    return names


def _assignments(
    seed: int,
    names: list[tuple[str, str]],
    answer_idx: int,
    runner_idx: int,
) -> dict[str, dict[str, str]]:
    del answer_idx, runner_idx
    result: dict[str, dict[str, str]] = {}
    for branch_idx, branch in enumerate(BRANCHES):
        statuses = _permutation(seed, f"{branch}:assignments", STATUS_BANK)
        step = (1, 5, 1, 5, 1, 5)[branch_idx % 6]
        offset = _pick(seed, f"{branch}:offset", len(statuses))
        result[branch] = {
            person_id: statuses[
                (offset + step * person_idx + branch_idx * (person_idx // len(statuses)))
                % len(statuses)
            ]
            for person_idx, (person_id, _label) in enumerate(names)
        }
    return result


def _checksum_plan(
    seed: int,
    status_by_person: dict[str, dict[str, str]],
    *,
    answer_id: str,
    runner_id: str,
) -> tuple[dict[str, int], tuple[int, ...], int, int, dict[str, int]]:
    status_order = _permutation(seed, "checksum-weights", STATUS_BANK)
    weights = {status: index for index, status in enumerate(status_order)}
    base_coefficients = (2, 3, 5, 7, 11, 13)
    start_value = 2 + seed % 17
    for attempt in range(64):
        coefficients = tuple(
            sorted(
                base_coefficients,
                key=lambda coefficient: hashlib.sha256(
                    f"{seed}:coefficient:{attempt}:{coefficient}".encode()
                ).digest(),
            )
        )
        for modulus in (97, 101, 103, 107, 109):
            checksums: dict[str, int] = {}
            for person_id, statuses in status_by_person.items():
                status_values = tuple(weights[statuses[branch]] for branch in BRANCHES)
                checksums[person_id] = iterated_checksum(
                    status_values,
                    coefficients,
                    start_value=start_value,
                    modulus=modulus,
                )
            checksum_values = list(checksums.values())
            if (
                checksum_values.count(checksums[answer_id]) == 1
                and checksum_values.count(checksums[runner_id]) == 1
                and checksums[answer_id] != checksums[runner_id]
            ):
                return weights, coefficients, start_value, modulus, checksums
    raise ValueError("could not construct unique checksum targets")


def iterated_checksum(
    values: tuple[int, ...],
    coefficients: tuple[int, ...],
    *,
    start_value: int,
    modulus: int,
) -> int:
    """Execute the disclosed forward/reverse/rotated nonlinear recurrence."""
    checksum = start_value
    passes = (
        (values, coefficients),
        (tuple(reversed(values)), tuple(reversed(coefficients))),
        (values, coefficients[1:] + coefficients[:1]),
    )
    for pass_values, pass_coefficients in passes:
        for value, coefficient in zip(
            pass_values,
            pass_coefficients,
            strict=True,
        ):
            checksum = (checksum * checksum + coefficient * value) % modulus
    return checksum


def _world(
    recipe: GenerationRecipe,
    names: list[tuple[str, str]],
    answer_id: str,
    family: FamilySpec,
) -> WorldSpec:
    return WorldSpec(
        id=f"world-{recipe.seed}",
        entities=[
            Entity(id=person_id, type="person", label=label, aliases=[label.split()[0]])
            for person_id, label in names
        ],
        relations=[],
        time_points=[TimePoint(id="t1", label="incident", order=1)],
        events=[
            Event(
                id="e_resolution",
                label=family.incident,
                actor=answer_id,
                time_point="t1",
                effects=["key_action"],
            )
        ],
        facts=[],
        target=TargetClaim(
            predicate="qualifies",
            arguments=["person"],
            expected_value=answer_id,
        ),
        intervention=Intervention(
            id="iv_checksum_key",
            description="replace the accepted checksum with the runner-up's checksum",
            disable_event="e_resolution",
            expected_target_value="none",
        ),
        answer_entity=answer_id,
        candidate_answers=[person_id for person_id, _ in names],
    )


def _questions(
    recipe: GenerationRecipe,
    family: FamilySpec,
    answer: str,
    runner: str,
    checksum_key: str,
    runner_checksum: str,
    runner_id: str,
) -> QuestionBundle:
    main = MAIN_STEMS[recipe.seed % len(MAIN_STEMS)].format(concept=family.concept)
    questions = [
        ScoredQuestion(
            id="q_main",
            question=main,
            gold_answer=answer,
            gold_answer_variants=name_answer_variants(answer),
            question_type="main",
        ),
        ScoredQuestion(
            id="q_near_match",
            question=(f"Whose six-stream checksum was {runner_checksum}? Give the full name."),
            gold_answer=runner,
            gold_answer_variants=name_answer_variants(runner),
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If the accepted checksum had been {runner_checksum} instead of "
                f"{checksum_key}, while every other record stayed fixed, who would become "
                f"the {family.concept}? Give the full name."
            ),
            gold_answer=runner,
            gold_answer_variants=name_answer_variants(runner),
            question_type="counterfactual",
        ),
        ScoredQuestion(
            id="q_protocol_key",
            question="What exact integer checksum did the board accept?",
            gold_answer=checksum_key,
            gold_answer_variants=[checksum_key],
            question_type="code",
        ),
    ]
    return QuestionBundle(
        main_question=main,
        gold_answer=answer,
        questions=questions,
        supported_conclusions=[
            f"{answer}'s six-stream checksum equals the accepted checksum.",
            f"{runner}'s six-stream checksum is {runner_checksum}.",
        ],
        counterfactual=CounterfactualTask(
            question=questions[2].question,
            answer=runner,
            intervention=f"replace checksum key with checksum assigned to {runner_id}",
        ),
        falsifier=FalsifierTask(
            hypothesis=f"{runner} matches the original checksum key",
            minimal_evidence=["f_checksum_formula", "f_checksum_key"],
        ),
    )


def _assignment_sentence(
    family: FamilySpec,
    branch: str,
    noun: str,
    label: str,
    value: str,
    variant: int,
) -> str:
    templates = {
        "relation": (
            "{label}'s signed {noun} review resolved to {value} status.",
            "A witness check left {label}'s {noun} at {value} status.",
            "The earlier pairing note gave {label} a {value} {noun} status.",
            "A damaged roster still assigned {value} status to {label}'s {noun}.",
            "On the sealed worksheet, {label}'s {noun} status was {value}.",
            "The review panel confirmed {value} status for {label}'s {noun}.",
        ),
        "temporal": (
            "{label}'s logged {noun} resolved to {value} status.",
            "The clock review gave {label}'s {noun} a {value} status.",
            "A clock-backed entry put {label}'s {noun} at {value} status.",
            "{label}'s verified {noun} carried {value} status.",
            "The sequence sheet assigned {value} status to {label}'s {noun}.",
            "After reconciliation, {label}'s {noun} status remained {value}.",
        ),
        "causal": (
            "{label}'s downstream {noun} resolved to {value} status.",
            "When {label} acted, instruments gave the {noun} {value} status.",
            "The {noun} traced to {label} carried {value} status.",
            "{label}'s action left the {noun} at {value} status.",
            "The causal review assigned {value} status to {label}'s {noun}.",
            "The {noun} following {label}'s step registered {value} status.",
        ),
        "spatial": (
            "{label}'s verified {noun} route resolved to {value} status.",
            "A door review gave {label}'s {noun} {value} status.",
            "The route sketch assigned {value} status to {label}'s {noun}.",
            "{label}'s {noun} location check resolved to {value} status.",
            "A witness check left {label}'s {noun} at {value} status.",
            "The movement ledger tied {label}'s {noun} to {value} status.",
        ),
        "sequence": (
            "{label}'s {noun} resolved to {value} status.",
            "The ordered log gave {label}'s {noun} {value} status.",
            "A sequence note placed {value} status beside {label}'s {noun}.",
            "{label}'s confirmed {noun} carried {value} status.",
            "The reconstruction assigned {value} status to {label}'s {noun}.",
            "At sequence review, {label}'s {noun} remained {value}.",
        ),
        "protocol": (
            "{label}'s sealed {noun} check resolved to {value} status.",
            "The token checked out to {label} gave the {noun} {value} status.",
            "A close photograph set {label}'s {noun} at {value} status.",
            "{label}'s acknowledged {noun} carried {value} status.",
            "The inventory recorded {value} status for {label}'s {noun}.",
            "At final count, {label}'s {noun} status remained {value}.",
        ),
    }
    template = templates[branch][variant % len(templates[branch])]
    return template.format(label=label, value=value, noun=noun)


def _visible(
    fact_id: str,
    text: str,
    atom: LogicAtom,
    scene_id: str,
    order: int,
) -> VisibleFact:
    return VisibleFact(
        id=fact_id,
        text=text,
        formal=f"atom:{atom.key}",
        channel=ClueChannel.RECORD,
        role="required",
        scene_id=scene_id,
        reveal_order=order,
    )


def _rule_visible(
    rule: LogicRule,
    text: str,
    scene_id: str,
    order: int,
) -> VisibleFact:
    return VisibleFact(
        id=f"f_rule_{rule.id}",
        text=text,
        formal=f"rule:{rule.id}",
        channel=ClueChannel.RULE_APPLICATION,
        role="required",
        scene_id=scene_id,
        reveal_order=order,
    )


def _offline_draft(
    recipe: GenerationRecipe,
    family: FamilySpec,
    facts: list[VisibleFact],
) -> StoryDraft:
    opening = (
        f"The record concerns {family.setting}. By the time investigators reconstructed "
        f"{family.incident}, casual impressions had produced several plausible candidates. "
        "The reviewers therefore used only the local rules stated in the surviving record."
    )
    scenes: list[SceneDraft] = []
    for scene_no in range(1, 6):
        scene_facts = sorted(
            (fact for fact in facts if fact.scene_id == f"sc{scene_no}"),
            key=lambda fact: fact.reveal_order,
        )
        connective = (
            "The inquiry moved from recollection to checked records. "
            if scene_no > 1
            else "Before comparing names, the panel read the governing notes aloud. "
        )
        scenes.append(
            SceneDraft(
                id=f"sc{scene_no}",
                title=f"Reconstruction {scene_no}",
                obligated_fact_ids=[fact.id for fact in scene_facts],
                prose=connective + " ".join(fact.text for fact in scene_facts),
            )
        )
    return StoryDraft(
        title=f"{family.concept.title()} — Case {recipe.seed}",
        opening=opening,
        scenes=scenes,
    )


def _pick(seed: int, salt: str, modulo: int) -> int:
    return hashlib.sha256(f"{seed}:{salt}".encode()).digest()[0] % modulo


def _permutation(seed: int, salt: str, values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            values,
            key=lambda value: hashlib.sha256(f"{seed}:{salt}:{value}".encode()).digest(),
        )
    )


__all__ = [
    "ConceptPuzzle",
    "FAMILIES",
    "build_concept_puzzle",
    "iterated_checksum",
]
