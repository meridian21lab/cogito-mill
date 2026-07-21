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

BRANCHES = ("relation", "temporal", "causal", "spatial", "sequence", "protocol")
VALUE_BANK = {
    "relation": ("amber", "cobalt", "ivory", "saffron", "violet", "silver"),
    "temporal": ("first", "second", "third", "fourth", "fifth", "sixth"),
    "causal": ("echo", "flare", "hush", "ripple", "spark", "wake"),
    "spatial": ("bridge", "court", "gallery", "harbor", "ridge", "vault"),
    "sequence": ("birch", "cedar", "elm", "larch", "pine", "yew"),
    "protocol": ("circle", "fork", "knot", "reed", "spire", "wave"),
}
CHANNEL_BANK = ("arch", "beacon", "cairn", "delta", "ember", "ford")
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
    "Reconstruct the six rule chains. Who qualifies as {concept}? Provide the full name.",
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
    accepted_outputs: dict[str, str] = {}
    runner_outputs: dict[str, str] = {}
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
        raw_values = VALUE_BANK[branch]
        channel_values = _permutation(recipe.seed, f"{branch}:channels", CHANNEL_BANK)
        status_values = _permutation(recipe.seed, f"{branch}:statuses", STATUS_BANK)
        raw_to_channel = dict(zip(raw_values, channel_values, strict=True))
        channel_to_status = dict(zip(channel_values, status_values, strict=True))
        used_raw_values = tuple(sorted(set(assignments[branch].values())))
        used_channels = tuple(raw_to_channel[value] for value in used_raw_values)
        accepted_output = channel_to_status[raw_to_channel[assignments[branch][answer_id]]]
        runner_output = channel_to_status[raw_to_channel[assignments[branch][runner_id]]]
        accepted_outputs[branch] = accepted_output
        runner_outputs[branch] = runner_output

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

        for map_idx, raw_value in enumerate(used_raw_values):
            channel = raw_to_channel[raw_value]
            atom = LogicAtom(
                predicate=f"{branch}_channel_map",
                arguments=[raw_value, channel],
            )
            logic_facts.append(atom)
            visible_facts.append(
                _visible(
                    f"f_{branch}_channel_{raw_value}",
                    (f"In the {noun} conversion legend, {raw_value} led to the {channel} channel."),
                    atom,
                    f"sc{1 + (map_idx + branch_idx) % 4}",
                    order,
                )
            )
            order += 1

        for map_idx, channel in enumerate(used_channels):
            status = channel_to_status[channel]
            atom = LogicAtom(
                predicate=f"{branch}_status_map",
                arguments=[channel, status],
            )
            logic_facts.append(atom)
            visible_facts.append(
                _visible(
                    f"f_{branch}_status_{channel}",
                    (f"For {noun}, the {channel} channel resolved to {status} status."),
                    atom,
                    f"sc{1 + (map_idx + branch_idx + 2) % 4}",
                    order,
                )
            )
            order += 1

        key_atom = LogicAtom(predicate=f"{branch}_key", arguments=[accepted_output])
        logic_facts.append(key_atom)
        visible_facts.append(
            _visible(
                f"f_{branch}_key",
                _key_sentence(family, branch, noun, accepted_output),
                key_atom,
                f"sc{2 + branch_idx % 3}",
                order,
            )
        )
        order += 1

        channel_rule = LogicRule(
            id=f"{branch}_trace_channel",
            premises=[
                LogicAtom(predicate=f"{branch}_link", arguments=["?person", "?raw"]),
                LogicAtom(
                    predicate=f"{branch}_channel_map",
                    arguments=["?raw", "?channel"],
                ),
            ],
            conclusion=LogicAtom(
                predicate=f"{branch}_channel",
                arguments=["?person", "?channel"],
            ),
            explanation=f"Translate a person's raw {noun} through the conversion legend.",
        )
        status_rule = LogicRule(
            id=f"{branch}_resolve_status",
            premises=[
                LogicAtom(
                    predicate=f"{branch}_channel",
                    arguments=["?person", "?channel"],
                ),
                LogicAtom(
                    predicate=f"{branch}_status_map",
                    arguments=["?channel", "?status"],
                ),
            ],
            conclusion=LogicAtom(
                predicate=f"{branch}_status",
                arguments=["?person", "?status"],
            ),
            explanation=f"Resolve the resulting {noun} channel to its status.",
        )
        match_rule = LogicRule(
            id=f"{branch}_match_key",
            premises=[
                LogicAtom(
                    predicate=f"{branch}_status",
                    arguments=["?person", "?status"],
                ),
                LogicAtom(predicate=f"{branch}_key", arguments=["?status"]),
            ],
            conclusion=LogicAtom(predicate=f"{branch}_mark", arguments=["?person"]),
            explanation=f"Compare the derived {noun} status with the accepted status.",
        )
        certify_rule = LogicRule(
            id=f"{branch}_certify",
            premises=[
                LogicAtom(predicate=f"{branch}_mark", arguments=["?person"]),
                LogicAtom(predicate="protocol_active"),
            ],
            conclusion=LogicAtom(predicate=f"{branch}_ok", arguments=["?person"]),
            explanation=f"Certify the matching {noun} mark under the active protocol.",
        )
        rules.extend([channel_rule, status_rule, match_rule, certify_rule])
        visible_facts.extend(
            [
                _rule_visible(
                    channel_rule,
                    (
                        f"The first {noun} rule required tracing each person's raw value "
                        "through the conversion legend to a channel."
                    ),
                    f"sc{1 + branch_idx % 2}",
                    order,
                ),
                _rule_visible(
                    status_rule,
                    (f"The second {noun} rule converted that channel into its listed status."),
                    f"sc{1 + branch_idx % 2}",
                    order + 1,
                ),
                _rule_visible(
                    match_rule,
                    (
                        f"The {noun} branch awarded a mark only when the derived status "
                        "equaled the accepted status."
                    ),
                    f"sc{1 + branch_idx % 2}",
                    order + 2,
                ),
                _rule_visible(
                    certify_rule,
                    (
                        f"A matching result for {noun} counted as certified only while "
                        "the incident protocol remained active."
                    ),
                    f"sc{1 + branch_idx % 2}",
                    order + 3,
                ),
            ]
        )
        order += 4

    final_rule = LogicRule(
        id=f"final_{family.id}",
        premises=[
            LogicAtom(predicate=f"{branch}_ok", arguments=["?person"]) for branch in BRANCHES
        ],
        conclusion=LogicAtom(predicate="qualifies", arguments=["?person"]),
        explanation=(f"The title {family.concept} requires all six independently certified marks."),
    )
    rules.append(final_rule)
    visible_facts.append(
        _rule_visible(
            final_rule,
            (
                f"The final definition was strict: the {family.concept} was one person who "
                "held all six certified marks—no five-mark near match qualified."
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
        accepted_outputs["protocol"],
        runner_outputs["protocol"],
        runner_id,
    )
    draft = _offline_draft(recipe, family, visible_facts)
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=visible,
        questions=questions,
        offline_draft=draft,
        n_hops=50,
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
        shift = 1 + branch_idx % (len(values) - 1)
        alternate = values[(values.index(accepted) + shift) % len(values)]
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
    protocol_noun = family.branch_nouns[-1]
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
                f"Who matched every branch except the {protocol_noun} branch? Give the full name."
            ),
            gold_answer=runner,
            gold_answer_variants=name_answer_variants(runner),
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If the accepted {protocol_noun} status had been {runner_protocol!r} instead of "
                f"{protocol_key!r}, while every other record stayed fixed, who would become "
                f"the {family.concept}? Give the full name."
            ),
            gold_answer=runner,
            gold_answer_variants=name_answer_variants(runner),
            question_type="counterfactual",
        ),
        ScoredQuestion(
            id="q_protocol_key",
            question=f"What exact one-word {protocol_noun} status did the board accept?",
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
            f"{answer} satisfies all six certified branches.",
            f"{runner} is the five-branch near match.",
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
        "spatial": (
            "{label}'s verified route ended in the {value} {noun}.",
            "A door record places {label} at the {value} {noun}.",
            "The route sketch assigns the {value} {noun} to {label}.",
            "{label}'s location check resolved to the {value} {noun}.",
            "A witness last saw {label} beside the {value} {noun}.",
            "The movement ledger ties {label} to the {value} {noun}.",
        ),
        "sequence": (
            "{label}'s action occupied the {value} {noun}.",
            "The ordered log gives {label} the {value} {noun}.",
            "A signed sequence note places the {value} {noun} beside {label}.",
            "{label}'s confirmed step carried the {value} {noun}.",
            "The reconstruction assigns the {value} {noun} to {label}.",
            "At sequence review, {label} retained the {value} {noun}.",
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


def _key_sentence(_family: FamilySpec, branch: str, noun: str, value: str) -> str:
    return f"The {branch} notice accepted {value} as the final {noun} status."


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


__all__ = ["ConceptPuzzle", "FAMILIES", "build_concept_puzzle"]
