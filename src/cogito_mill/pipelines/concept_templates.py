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

BRANCHES = ("relation", "temporal", "causal", "protocol")
VALUE_BANK = {
    "relation": ("amber", "cobalt", "ivory", "saffron", "violet", "silver"),
    "temporal": ("first", "second", "third", "fourth", "fifth", "sixth"),
    "causal": ("echo", "flare", "hush", "ripple", "spark", "wake"),
    "protocol": ("circle", "fork", "knot", "reed", "spire", "wave"),
}


@dataclass(frozen=True)
class FamilySpec:
    id: str
    concept: str
    setting: str
    incident: str
    branch_nouns: tuple[str, str, str, str]


FAMILIES = (
    FamilySpec(
        "watch_handover",
        "concordant watchkeeper",
        "an icebound research vessel changing watches during a storm",
        "the emergency ballast release",
        ("mentor pennant", "watch interval", "alarm consequence", "seal notch"),
    ),
    FamilySpec(
        "archive_provenance",
        "true chain custodian",
        "a monastic archive moving manuscripts before a flood",
        "the protected folio's final transfer",
        ("copying lineage", "bell interval", "wax reaction", "cord pattern"),
    ),
    FamilySpec(
        "fault_network",
        "convergent responder",
        "an orbital habitat tracing a cascading cooling fault",
        "the isolation command that restored the habitat",
        ("relay affiliation", "diagnostic interval", "downstream symptom", "breaker mark"),
    ),
    FamilySpec(
        "delegated_authority",
        "valid emergency delegate",
        "a city museum evacuating its collection during a power failure",
        "the lawful release of the sealed collection",
        ("deputy chain", "authority window", "release consequence", "witness token"),
    ),
    FamilySpec(
        "expedition_signal",
        "coherent signal bearer",
        "a desert expedition decoding a chain of emergency beacons",
        "the transmission that redirected the rescue convoy",
        ("team pairing", "signal interval", "repeater response", "cipher glyph"),
    ),
    FamilySpec(
        "workshop_provenance",
        "certified restoration lead",
        "a conservation workshop tracing a damaged artifact through several rooms",
        "the treatment that stabilized the artifact",
        ("apprentice lineage", "work interval", "chemical response", "tool stamp"),
    ),
)

MAIN_STEMS = (
    "Under the local rules, who alone became the {concept}? Give the full name.",
    "Which participant satisfies every condition for {concept}? Answer with the full name.",
    "Reconstruct the four rule chains. Who qualifies as {concept}? Provide the full name.",
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
    accepted = {branch: assignments[branch][answer_id] for branch in BRANCHES}
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
        for person_idx, (person_id, label) in enumerate(names):
            value = assignments[branch][person_id]
            atom = LogicAtom(predicate=f"{branch}_link", arguments=[person_id, value])
            logic_facts.append(atom)
            visible_facts.append(
                _visible(
                    f"f_{branch}_{person_id}",
                    _assignment_sentence(family, branch, noun, label, value, person_idx),
                    atom,
                    f"sc{2 + (branch_idx + person_idx) % 3}",
                    order,
                )
            )
            order += 1

        key_atom = LogicAtom(predicate=f"{branch}_key", arguments=[accepted[branch]])
        logic_facts.append(key_atom)
        visible_facts.append(
            _visible(
                f"f_{branch}_key",
                _key_sentence(family, branch, noun, accepted[branch]),
                key_atom,
                f"sc{2 + branch_idx % 3}",
                order,
            )
        )
        order += 1

        mark_rule = LogicRule(
            id=f"{branch}_match",
            premises=[
                LogicAtom(predicate=f"{branch}_link", arguments=["?person", "?value"]),
                LogicAtom(predicate=f"{branch}_key", arguments=["?value"]),
            ],
            conclusion=LogicAtom(predicate=f"{branch}_mark", arguments=["?person"]),
            explanation=f"Match a person's {noun} value to the incident's accepted value.",
        )
        ok_rule = LogicRule(
            id=f"{branch}_certify",
            premises=[
                LogicAtom(predicate=f"{branch}_mark", arguments=["?person"]),
                LogicAtom(predicate="protocol_active"),
            ],
            conclusion=LogicAtom(predicate=f"{branch}_ok", arguments=["?person"]),
            explanation=f"An active protocol turns the matching {noun} into a certified mark.",
        )
        rules.extend([mark_rule, ok_rule])
        visible_facts.extend(
            [
                _rule_visible(
                    mark_rule,
                    (
                        f"The board's {noun} rule said that a person's recorded value had to "
                        "equal the accepted value for this incident; only then did that branch "
                        "receive a mark."
                    ),
                    f"sc{1 + branch_idx % 2}",
                    order,
                ),
                _rule_visible(
                    ok_rule,
                    (
                        f"A matching {noun} counted as certified only while the incident "
                        "protocol remained active."
                    ),
                    f"sc{1 + branch_idx % 2}",
                    order + 1,
                ),
            ]
        )
        order += 2

    final_rule = LogicRule(
        id=f"final_{family.id}",
        premises=[
            LogicAtom(predicate=f"{branch}_ok", arguments=["?person"]) for branch in BRANCHES
        ],
        conclusion=LogicAtom(predicate="qualifies", arguments=["?person"]),
        explanation=(
            f"The title {family.concept} requires all four independently certified marks."
        ),
    )
    rules.append(final_rule)
    visible_facts.append(
        _rule_visible(
            final_rule,
            (
                f"The final definition was strict: the {family.concept} was one person who "
                "held all four certified marks—no three-mark near match qualified."
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
        accepted["protocol"],
        assignments["protocol"][runner_id],
        runner_id,
    )
    draft = _offline_draft(recipe, family, visible_facts)
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=visible,
        questions=questions,
        offline_draft=draft,
        n_hops=13,
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
    result: dict[str, dict[str, str]] = {}
    for branch_idx, branch in enumerate(BRANCHES):
        values = VALUE_BANK[branch]
        accepted = values[_pick(seed, f"{branch}:accepted", len(values))]
        alternate = values[(values.index(accepted) + 1 + branch_idx) % len(values)]
        branch_values: dict[str, str] = {}
        for idx, (person_id, _label) in enumerate(names):
            passes = idx == answer_idx or (
                idx != runner_idx and (idx + branch_idx) % len(BRANCHES) != 0
            )
            if idx == runner_idx:
                passes = branch != "protocol"
            branch_values[person_id] = (
                accepted
                if passes
                else values[(values.index(alternate) + idx + branch_idx) % len(values)]
            )
            if not passes and branch_values[person_id] == accepted:
                branch_values[person_id] = alternate
        result[branch] = branch_values
    return result


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
            id="iv_protocol_key",
            description="replace the accepted protocol value with the runner-up's value",
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
    protocol_key: str,
    runner_protocol: str,
    runner_id: str,
) -> QuestionBundle:
    main = MAIN_STEMS[recipe.seed % len(MAIN_STEMS)].format(concept=family.concept)
    relation_noun, temporal_noun, causal_noun, protocol_noun = family.branch_nouns
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
            question=(
                f"Who matched the {relation_noun}, {temporal_noun}, and {causal_noun} "
                f"branches but failed only the {protocol_noun} branch? Give the full name."
            ),
            gold_answer=runner,
            gold_answer_variants=name_answer_variants(runner),
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If the accepted {protocol_noun} value had been {runner_protocol!r} instead of "
                f"{protocol_key!r}, while every other record stayed fixed, who would become "
                f"the {family.concept}? Give the full name."
            ),
            gold_answer=runner,
            gold_answer_variants=name_answer_variants(runner),
            question_type="counterfactual",
        ),
        ScoredQuestion(
            id="q_protocol_key",
            question=f"What exact one-word {protocol_noun} value did the board accept?",
            gold_answer=protocol_key,
            gold_answer_variants=[protocol_key],
            question_type="code",
        ),
    ]
    return QuestionBundle(
        main_question=main,
        gold_answer=answer,
        questions=questions,
        supported_conclusions=[
            f"{answer} satisfies all four certified branches.",
            f"{runner} is the three-branch near match.",
        ],
        counterfactual=CounterfactualTask(
            question=questions[2].question,
            answer=runner,
            intervention=f"replace protocol key with value assigned to {runner_id}",
        ),
        falsifier=FalsifierTask(
            hypothesis=f"{runner} satisfies the original protocol",
            minimal_evidence=[f"f_protocol_{runner_id}", "f_protocol_key"],
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
            "{label}'s signed handover bears the {value} {noun}.",
            "A witness remembers the {value} {noun} beside {label}'s name.",
            "The earlier pairing note gives {label} the {value} {noun}.",
            "A damaged roster still links the {value} {noun} to {label}.",
            "On the sealed worksheet, {label} is paired with the {value} {noun}.",
            "The review panel confirms that {label}'s {noun} was {value}.",
        ),
        "temporal": (
            "{label} completed the logged duty in the {value} {noun}.",
            "The {value} {noun} was the period in which {label} signed the handover.",
            "A clock-backed entry puts {label}'s work in the {value} {noun}.",
            "{label}'s only verified activity falls inside the {value} {noun}.",
            "The sequence sheet assigns the {value} {noun} to {label}.",
            "After the timings were reconciled, {label} remained in the {value} {noun}.",
        ),
        "causal": (
            "{label}'s intervention produced the {value} {noun} downstream.",
            "When {label} acted, instruments registered the {value} {noun}.",
            "The consequence traced to {label} was the {value} {noun}.",
            "{label}'s action propagated until it caused the {value} {noun}.",
            "The causal review attributes the {value} {noun} to {label}'s action.",
            "Only the {value} {noun} followed from the step performed by {label}.",
        ),
        "protocol": (
            "{label}'s sealed kit carried the {value} {noun}.",
            "The token checked out to {label} displayed the {value} {noun}.",
            "A close photograph shows the {value} {noun} on {label}'s tag.",
            "{label} acknowledged receiving the {value} {noun}.",
            "The inventory records the {value} {noun} against {label}.",
            "At final count, {label} still held the {value} {noun}.",
        ),
    }
    template = templates[branch][variant % len(templates[branch])]
    return template.format(label=label, value=value, noun=noun)


def _key_sentence(family: FamilySpec, branch: str, noun: str, value: str) -> str:
    forms = {
        "relation": (
            f"The relation notice recognized the {value} {noun} and no other affiliation."
        ),
        "temporal": f"The timing rule selected the {value} {noun} as the valid window.",
        "causal": f"The causal test required the {value} {noun} as its downstream result.",
        "protocol": f"The protocol sheet accepted the {value} {noun} as its exact token.",
    }
    return forms[branch]


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


__all__ = ["ConceptPuzzle", "FAMILIES", "build_concept_puzzle"]
