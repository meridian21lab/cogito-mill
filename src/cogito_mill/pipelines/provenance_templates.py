"""Connected custody-provenance puzzles with deterministic clue ablations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from cogito_mill.domain.appendix import (
    EvidenceIntervention,
    ProvenanceState,
    SolverAppendix,
)
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
from cogito_mill.reasoning.logic import goal_candidates, proof_keys

if TYPE_CHECKING:
    from cogito_mill.pipelines.concept_templates import ConceptPuzzle, FamilySpec


class AddFact(Protocol):
    def __call__(
        self,
        fact_id: str,
        text: str,
        formal: str,
        *,
        scene_id: str,
        channel: ClueChannel,
        role: str = "required",
    ) -> None: ...


@dataclass(frozen=True)
class ProvenanceFlavor:
    token: str
    containers: tuple[str, str, str]
    checkpoint: str
    authorization: str


@dataclass(frozen=True)
class CustodyEvent:
    id: str
    kind: str
    minute: int
    actor_id: str
    container_id: str | None
    source_container_id: str | None
    destination_container_id: str | None
    from_person_id: str | None
    to_person_id: str | None
    fact_id: str
    text: str


FLAVORS: dict[str, ProvenanceFlavor] = {
    "festival_theft": ProvenanceFlavor(
        token="numbered jeweler's release seal",
        containers=("amber receipt wallet", "blue vendor pouch", "cedar display case"),
        checkpoint="boutique's closing reader",
        authorization="opened the diamond case",
    ),
    "archive_theft": ProvenanceFlavor(
        token="bronze archive seal",
        containers=("reed document tube", "blue folio satchel", "cedar reliquary box"),
        checkpoint="scriptorium seal reader",
        authorization="released the protected folio",
    ),
    "habitat_sabotage": ProvenanceFlavor(
        token="ceramic command wafer",
        containers=("orange service pouch", "grey tool cassette", "clear sample case"),
        checkpoint="ring-three command reader",
        authorization="issued the isolation command",
    ),
    "museum_release": ProvenanceFlavor(
        token="numbered gallery release key",
        containers=("canvas registrar wallet", "blue transit satchel", "black conservation case"),
        checkpoint="sealed-gallery release reader",
        authorization="released the sealed collection",
    ),
    "convoy_diversion": ProvenanceFlavor(
        token="brass relay cipher",
        containers=("sand-colored map wallet", "blue radio pouch", "cedar instrument case"),
        checkpoint="relay transmitter",
        authorization="sent the false transmission",
    ),
    "workshop_switch": ProvenanceFlavor(
        token="engraved treatment-room seal",
        containers=("linen receipt wallet", "blue tool satchel", "cedar pigment case"),
        checkpoint="treatment-room seal reader",
        authorization="approved the dial substitution",
    ),
}

MAIN_STEMS = (
    "Whose custody chain ends with the {token} at the {checkpoint}? Give the full name.",
    "Trace the sealed handoffs. Who held the {token} when it reached the {checkpoint}? "
    "Give the full name.",
    "Which full name belongs to the final custodian of the {token} at the time of the incident?",
    "The {token} authorized the incident. Who had custody of it at that moment? "
    "Give the full name.",
    "After following every witnessed handoff and contents transfer, who carried the {token} at the "
    "final checkpoint? Give the full name.",
    "Who signed for the container that held the {token} when the authorization was recorded? "
    "Give the full name.",
    "Reconstruct the provenance of the {token}. Which person was its final custodian? "
    "Give the full name.",
    "Which full name is forced by the connected custody record for the {token}?",
    "Who possessed the container holding the {token} when the {checkpoint} logged it? "
    "Give the full name.",
    "Follow the token rather than the people. With whom did the {token} finish? "
    "Give the full name.",
    "Which person received the final live container in the {token} custody chain? "
    "Give the full name.",
    "Who was responsible for the final custody of the {token} when it authorized the incident? "
    "Give the full name.",
)


def build_provenance_puzzle(recipe: GenerationRecipe) -> ConceptPuzzle:
    """Build a proof-carrying custody DAG without answer-specific goal facts."""
    from cogito_mill.pipelines.concept_templates import (
        ConceptPuzzle,
        _first_name,
        _names,
        _pick,
        _surname,
        family_for_seed,
        minutes_to_clock,
    )

    family = family_for_seed(recipe.seed)
    flavor = FLAVORS[family.id]
    names = _names(recipe.seed, recipe.n_suspects)
    labels = dict(names)
    person_ids = [person_id for person_id, _ in names]
    container_ids = [f"container_{index}" for index in range(3)]
    container_labels = dict(zip(container_ids, flavor.containers, strict=True))
    token_id = "authorization_token"
    start_minute = 13 * 60 + 5 + (recipe.seed % 4) * 3

    base = recipe.seed % len(person_ids)
    carriers = {
        container_id: person_ids[(base + index) % len(person_ids)]
        for index, container_id in enumerate(container_ids)
    }
    token_container = container_ids[_pick(recipe.seed, "token-container", len(container_ids))]

    visible_facts: list[VisibleFact] = []
    logic_facts: list[LogicAtom] = []
    rules: list[LogicRule] = []
    order = 1

    def add_fact(
        fact_id: str,
        text: str,
        formal: str,
        *,
        scene_id: str,
        channel: ClueChannel,
        role: str = "required",
    ) -> None:
        nonlocal order
        visible_facts.append(
            VisibleFact(
                id=fact_id,
                text=text,
                formal=formal,
                channel=channel,
                role=role,
                scene_id=scene_id,
                reveal_order=order,
            )
        )
        order += 1

    for container_id in container_ids:
        holder_id = carriers[container_id]
        holder = labels[holder_id]
        atom = LogicAtom(predicate="carrier", arguments=[container_id, holder_id, "0"])
        logic_facts.append(atom)
        add_fact(
            f"f_initial_{container_id}",
            (
                f"At {minutes_to_clock(start_minute - 12)}, {_first_name(holder)} signed for "
                f"the {container_labels[container_id]}."
            ),
            f"atom:{atom.key}",
            scene_id="sc1",
            channel=ClueChannel.RECORD,
        )

    token_atom = LogicAtom(predicate="contains", arguments=[token_id, token_container, "0"])
    logic_facts.append(token_atom)
    add_fact(
        "f_initial_token",
        (
            f"The opening inspection placed the {flavor.token} inside the "
            f"{container_labels[token_container]}, whose seam was then witnessed closed."
        ),
        f"atom:{token_atom.key}",
        scene_id="sc1",
        channel=ClueChannel.PHYSICAL_STATE,
    )

    for index, (person_id, label) in enumerate(names):
        add_fact(
            f"f_surname_{person_id}",
            f"The duty book records {_first_name(label)} under the surname {_surname(label)}.",
            f"name:{person_id}",
            scene_id=f"sc{1 + index % 4}",
            channel=ClueChannel.RECORD,
        )

    add_fact(
        "f_shared_access",
        (
            f"The access log placed every named custodian inside {family.setting} during the "
            "final interval, so doorway opportunity alone did not distinguish them."
        ),
        "context:shared_access",
        scene_id="sc2",
        channel=ClueChannel.RECORD,
        role="context",
    )

    events: list[CustodyEvent] = []
    snapshots: list[ProvenanceState] = [
        _snapshot(
            0,
            token_container,
            carriers,
            container_labels,
            labels,
            event_fact_id=None,
            summary="Opening witnessed custody state.",
        )
    ]
    step = 0
    current_container = token_container

    def next_holder(current_holder: str, cycle: int) -> str:
        preferred = (base + cycle + 3) % len(person_ids)
        for offset in range(len(person_ids)):
            candidate = person_ids[(preferred + offset) % len(person_ids)]
            if candidate != current_holder:
                return candidate
        raise ValueError("provenance puzzle needs at least two people")

    for cycle in range(7):
        current_holder = carriers[current_container]
        destinations = [
            container_id
            for container_id in container_ids
            if container_id != current_container and carriers[container_id] != current_holder
        ]
        if not destinations:
            raise ValueError("no independently held destination container")
        destination = destinations[(recipe.seed + cycle) % len(destinations)]

        step += 1
        event = _handoff_event(
            step=step,
            minute=start_minute + step * 7,
            container_id=destination,
            from_person_id=carriers[destination],
            to_person_id=current_holder,
            container_labels=container_labels,
            labels=labels,
            minutes_to_clock=minutes_to_clock,
        )
        token_container, carriers = _apply_event(
            event,
            token_id=token_id,
            token_container=token_container,
            carriers=carriers,
            logic_facts=logic_facts,
            rules=rules,
            add_fact=add_fact,
        )
        events.append(event)
        snapshots.append(
            _snapshot(
                step,
                token_container,
                carriers,
                container_labels,
                labels,
                event_fact_id=event.fact_id,
                summary=event.text,
            )
        )

        step += 1
        event = _contents_transfer_event(
            step=step,
            minute=start_minute + step * 7,
            source_container_id=current_container,
            destination_container_id=destination,
            actor_id=current_holder,
            container_labels=container_labels,
            labels=labels,
            minutes_to_clock=minutes_to_clock,
        )
        token_container, carriers = _apply_event(
            event,
            token_id=token_id,
            token_container=token_container,
            carriers=carriers,
            logic_facts=logic_facts,
            rules=rules,
            add_fact=add_fact,
        )
        events.append(event)
        snapshots.append(
            _snapshot(
                step,
                token_container,
                carriers,
                container_labels,
                labels,
                event_fact_id=event.fact_id,
                summary=event.text,
            )
        )
        current_container = destination

        step += 1
        new_holder = next_holder(current_holder, cycle)
        event = _handoff_event(
            step=step,
            minute=start_minute + step * 7,
            container_id=current_container,
            from_person_id=current_holder,
            to_person_id=new_holder,
            container_labels=container_labels,
            labels=labels,
            minutes_to_clock=minutes_to_clock,
        )
        token_container, carriers = _apply_event(
            event,
            token_id=token_id,
            token_container=token_container,
            carriers=carriers,
            logic_facts=logic_facts,
            rules=rules,
            add_fact=add_fact,
        )
        events.append(event)
        snapshots.append(
            _snapshot(
                step,
                token_container,
                carriers,
                container_labels,
                labels,
                event_fact_id=event.fact_id,
                summary=event.text,
            )
        )

    answer_id = carriers[token_container]
    answer_label = labels[answer_id]
    final_minute = start_minute + (step + 2) * 7
    signature_atom = LogicAtom(predicate="authorized", arguments=[token_id, str(step)])
    logic_facts.append(signature_atom)
    add_fact(
        "f_final_authorization",
        (
            f"At {minutes_to_clock(final_minute)}, the {flavor.checkpoint} recorded the unique "
            f"imprint of the {flavor.token}; that token {flavor.authorization}."
        ),
        f"atom:{signature_atom.key}",
        scene_id="sc5",
        channel=ClueChannel.RECORD,
    )
    final_rule = LogicRule(
        id="relation_final_provenance",
        premises=[
            signature_atom,
            LogicAtom(predicate="contains", arguments=[token_id, "?container", str(step)]),
            LogicAtom(predicate="carrier", arguments=["?container", "?person", str(step)]),
        ],
        conclusion=LogicAtom(predicate="qualifies", arguments=["?person"]),
        explanation=(
            "The authorization imprint identifies the tracked token; its final container and "
            "that container's final carrier identify the custodian."
        ),
    )
    rules.append(final_rule)
    add_fact(
        "f_rule_provenance",
        (
            "The checkpoint accepted only that uniquely numbered token, and the witnessed "
            "custody record remained sealed between each stated handoff."
        ),
        f"rule:{final_rule.id}",
        scene_id="sc5",
        channel=ClueChannel.RULE_APPLICATION,
    )

    distractor_people = [person_id for person_id in person_ids if person_id != answer_id]
    if len(distractor_people) >= 2:
        left, right = distractor_people[:2]
        add_fact(
            "f_decoy_transfer",
            (
                f"At {minutes_to_clock(start_minute + 37)}, {_first_name(labels[left])} lent "
                f"{_first_name(labels[right])} a silver visitor badge beside the public desk."
            ),
            "distractor:visitor_badge",
            scene_id="sc3",
            channel=ClueChannel.OBSERVATION,
            role="distractor",
        )

    theory = LogicTheory(facts=logic_facts, rules=rules)
    survivors = goal_candidates(theory, person_ids)
    if survivors != [answer_id]:
        raise ValueError(f"provenance construction is not unique: {survivors}")
    goal = LogicAtom(predicate=theory.goal_predicate, arguments=[answer_id])
    proof_atom_keys = set(proof_keys(theory, goal))
    critical_fact_ids = [
        fact.id
        for fact in visible_facts
        if fact.formal.startswith("atom:") and fact.formal.removeprefix("atom:") in proof_atom_keys
    ]
    _assert_key_clue_ablation(
        theory=theory,
        visible_facts=visible_facts,
        critical_fact_ids=critical_fact_ids,
        candidates=person_ids,
        answer_id=answer_id,
    )

    final_event = events[-1]
    assert final_event.kind == "handoff"
    counterfactual_id = next(person_id for person_id in person_ids if person_id != answer_id)
    counterfactual_label = labels[counterfactual_id]
    intervention = EvidenceIntervention(
        person_id=counterfactual_id,
        person_label=counterfactual_label,
        fact_id=final_event.fact_id,
        description=(
            f"{counterfactual_label}, rather than {answer_label}, had signed for the "
            f"{container_labels[token_container]} in the final witnessed handoff"
        ),
        answer_label=counterfactual_label,
        secondary_person_id=answer_id,
        secondary_person_label=answer_label,
    )
    questions = _questions(
        recipe=recipe,
        flavor=flavor,
        answer_label=answer_label,
        counterfactual_label=counterfactual_label,
        intervention=intervention,
        events=events,
        snapshots=snapshots,
    )
    falsifier = FalsifierTask(
        hypothesis=f"{counterfactual_label} held the authorization token at the checkpoint",
        minimal_evidence=[final_event.fact_id, "f_final_authorization"],
    )
    questions = questions.model_copy(update={"falsifier": falsifier})
    appendix = SolverAppendix(
        id=f"lss-concept-{recipe.seed:06d}",
        mechanism="provenance_custody_dag",
        incident={
            "family": family.id,
            "incident": family.incident,
            "checkpoint": flavor.checkpoint,
            "authorization_token": flavor.token,
            "final_step": step,
            "critical_fact_ids": critical_fact_ids,
        },
        provenance_states=snapshots,
        opportunity={label: True for _, label in names},
        supported_conclusions=questions.supported_conclusions,
        evidence_counterfactual=intervention,
        falsifier=falsifier,
        notes=[
            "Every named person has local access; custody provenance, not opportunity, decides.",
            "Removing any listed critical fact prevents the same unique visible answer.",
        ],
    )
    world = _world(
        recipe=recipe,
        names=names,
        answer_id=answer_id,
        counterfactual_id=counterfactual_id,
        family=family,
        final_minute=final_minute,
    )
    draft = _offline_draft(
        family=family,
        flavor=flavor,
        visible_facts=visible_facts,
        final_minute=final_minute,
    )
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=VisibleTheory(
            id=f"vis-{recipe.seed}",
            world_id=f"world-{recipe.seed}",
            facts=visible_facts,
            logic=theory,
        ),
        questions=questions,
        offline_draft=draft,
        n_hops=len(proof_atom_keys),
        appendix=appendix,
        setting_family=family.setting_family,
    )


def _handoff_event(
    *,
    step: int,
    minute: int,
    container_id: str,
    from_person_id: str,
    to_person_id: str,
    container_labels: dict[str, str],
    labels: dict[str, str],
    minutes_to_clock: Callable[[int], str],
) -> CustodyEvent:
    clock = minutes_to_clock(minute)
    from_first = labels[from_person_id].split()[0]
    to_first = labels[to_person_id].split()[0]
    frames = (
        (
            "At {clock}, {sender} set the {container} beside {recipient}'s work; "
            "{recipient} signed the receipt before carrying it away."
        ),
        (
            "{recipient} took custody of the {container} from {sender} at {clock}, as the "
            "witness noted beside the container's seam number."
        ),
        (
            "The {clock} entry records {sender} surrendering the {container} to {recipient}; "
            "the recipient's mark appears on that same entry."
        ),
        (
            "A witness watched {recipient} accept the {container} from {sender} at {clock} "
            "and carry it toward the next ordinary task."
        ),
        (
            "When the clock showed {clock}, {sender} passed custody of the {container} to "
            "{recipient}, who checked the seam and signed."
        ),
        (
            "{sender}'s responsibility for the {container} ended at {clock}, when {recipient} "
            "accepted it under the witness's eye."
        ),
    )
    text = frames[step % len(frames)].format(
        clock=clock,
        sender=from_first,
        recipient=to_first,
        container=container_labels[container_id],
    )
    return CustodyEvent(
        id=f"e_{step:02d}",
        kind="handoff",
        minute=minute,
        actor_id=from_person_id,
        container_id=container_id,
        source_container_id=None,
        destination_container_id=None,
        from_person_id=from_person_id,
        to_person_id=to_person_id,
        fact_id=f"f_event_{step:02d}",
        text=text,
    )


def _contents_transfer_event(
    *,
    step: int,
    minute: int,
    source_container_id: str,
    destination_container_id: str,
    actor_id: str,
    container_labels: dict[str, str],
    labels: dict[str, str],
    minutes_to_clock: Callable[[int], str],
) -> CustodyEvent:
    clock = minutes_to_clock(minute)
    actor_first = labels[actor_id].split()[0]
    frames = (
        (
            "At {clock}, {actor} broke the two witness tapes and tipped everything from the "
            "{source} into the {destination}; nobody inventoried the contents before the new "
            "seam was closed."
        ),
        (
            "During the {clock} check, {actor} emptied the {source} into the {destination} "
            "without taking out or naming any individual object, then sealed the destination."
        ),
        (
            "The receipt marked {clock}: {actor} transferred the complete, unexamined contents "
            "of the {source} to the {destination}, leaving the source empty."
        ),
        (
            "Witnesses at {clock} saw {actor} pour the still-unlisted contents of the {source} "
            "into the {destination} and fasten the destination's numbered seam."
        ),
    )
    text = frames[step % len(frames)].format(
        clock=clock,
        actor=actor_first,
        source=container_labels[source_container_id],
        destination=container_labels[destination_container_id],
    )
    return CustodyEvent(
        id=f"e_{step:02d}",
        kind="contents_transfer",
        minute=minute,
        actor_id=actor_id,
        container_id=None,
        source_container_id=source_container_id,
        destination_container_id=destination_container_id,
        from_person_id=None,
        to_person_id=None,
        fact_id=f"f_event_{step:02d}",
        text=text,
    )


def _apply_event(
    event: CustodyEvent,
    *,
    token_id: str,
    token_container: str,
    carriers: dict[str, str],
    logic_facts: list[LogicAtom],
    rules: list[LogicRule],
    add_fact: AddFact,
) -> tuple[str, dict[str, str]]:
    prior_step = event.id.removeprefix("e_")
    previous_index = str(int(prior_step) - 1)
    current_index = str(int(prior_step))
    before_carriers = dict(carriers)
    before_container = token_container
    event_atom = LogicAtom(predicate="observed_event", arguments=[event.id])
    logic_facts.append(event_atom)
    scene_id = f"sc{min(4, 2 + (int(current_index) - 1) // 7)}"
    add_fact(
        event.fact_id,
        event.text,
        f"atom:{event_atom.key}",
        scene_id=scene_id,
        channel=ClueChannel.OBSERVATION,
    )

    if event.kind == "handoff":
        assert event.container_id is not None
        assert event.from_person_id is not None
        assert event.to_person_id is not None
        if carriers[event.container_id] != event.from_person_id:
            raise ValueError("handoff source does not carry the container")
        carriers = dict(carriers)
        carriers[event.container_id] = event.to_person_id
    elif event.kind == "contents_transfer":
        assert event.source_container_id is not None
        assert event.destination_container_id is not None
        if token_container != event.source_container_id:
            raise ValueError("content-transfer source does not contain the token")
        actor = event.actor_id
        if (
            carriers[event.source_container_id] != actor
            or carriers[event.destination_container_id] != actor
        ):
            raise ValueError("content-transfer containers are not co-located with the actor")
        token_container = event.destination_container_id
    else:
        raise ValueError(f"unknown custody event kind: {event.kind}")

    for container_id, prior_holder in before_carriers.items():
        next_holder = carriers[container_id]
        premises = [
            LogicAtom(
                predicate="carrier",
                arguments=[container_id, prior_holder, previous_index],
            )
        ]
        if prior_holder != next_holder:
            premises.append(event_atom)
        rules.append(
            LogicRule(
                id=f"relation_carrier_{event.id}_{container_id}",
                premises=premises,
                conclusion=LogicAtom(
                    predicate="carrier",
                    arguments=[container_id, next_holder, current_index],
                ),
                explanation=(
                    f"Propagate {container_id}'s witnessed carrier through custody event "
                    f"{event.id}."
                ),
            )
        )

    contain_premises = [
        LogicAtom(
            predicate="contains",
            arguments=[token_id, before_container, previous_index],
        )
    ]
    if before_container != token_container:
        assert event.source_container_id is not None
        assert event.destination_container_id is not None
        contain_premises.extend(
            [
                LogicAtom(
                    predicate="carrier",
                    arguments=[event.source_container_id, event.actor_id, previous_index],
                ),
                LogicAtom(
                    predicate="carrier",
                    arguments=[event.destination_container_id, event.actor_id, previous_index],
                ),
                event_atom,
            ]
        )
    rules.append(
        LogicRule(
            id=f"relation_contains_{event.id}",
            premises=contain_premises,
            conclusion=LogicAtom(
                predicate="contains",
                arguments=[token_id, token_container, current_index],
            ),
            explanation=f"Propagate the token's sealed container through custody event {event.id}.",
        )
    )
    return token_container, carriers


def _snapshot(
    step: int,
    token_container: str,
    carriers: dict[str, str],
    container_labels: dict[str, str],
    labels: dict[str, str],
    *,
    event_fact_id: str | None,
    summary: str,
) -> ProvenanceState:
    return ProvenanceState(
        step=step,
        token_container=container_labels[token_container],
        carriers={container_labels[key]: labels[value] for key, value in carriers.items()},
        event_fact_id=event_fact_id,
        summary=summary,
    )


def _assert_key_clue_ablation(
    *,
    theory: LogicTheory,
    visible_facts: list[VisibleFact],
    critical_fact_ids: list[str],
    candidates: list[str],
    answer_id: str,
) -> None:
    facts_by_id = {fact.id: fact for fact in visible_facts}
    if len(critical_fact_ids) < 10:
        raise ValueError("provenance proof is too shallow for the development target")
    for fact_id in critical_fact_ids:
        atom_key = facts_by_id[fact_id].formal.removeprefix("atom:")
        reduced = theory.model_copy(
            update={"facts": [atom for atom in theory.facts if atom.key != atom_key]}
        )
        if goal_candidates(reduced, candidates) == [answer_id]:
            raise ValueError(f"critical clue ablation preserved the answer: {fact_id}")


def _questions(
    *,
    recipe: GenerationRecipe,
    flavor: ProvenanceFlavor,
    answer_label: str,
    counterfactual_label: str,
    intervention: EvidenceIntervention,
    events: list[CustodyEvent],
    snapshots: list[ProvenanceState],
) -> QuestionBundle:
    from cogito_mill.pipelines.concept_templates import _pick

    main = MAIN_STEMS[_pick(recipe.seed, "provenance-stem", len(MAIN_STEMS))].format(
        token=flavor.token,
        checkpoint=flavor.checkpoint,
    )
    transfers = [event for event in events if event.kind == "contents_transfer"]
    probe = transfers[1]
    probe_state = snapshots[int(probe.id.removeprefix("e_"))]
    questions = [
        ScoredQuestion(
            id="q_main",
            question=main,
            gold_answer=answer_label,
            gold_answer_variants=name_answer_variants(answer_label),
            question_type="main",
        ),
        ScoredQuestion(
            id="q_provenance_checkpoint",
            question=(
                f"Immediately after the second witnessed contents transfer, which container "
                f"held the "
                f"{flavor.token}? Answer with the container description only."
            ),
            gold_answer=probe_state.token_container,
            gold_answer_variants=[probe_state.token_container],
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If {intervention.description}, while every earlier handoff and contents "
                f"transfer stayed fixed, who would hold the {flavor.token} at the checkpoint? "
                "Give the full name."
            ),
            gold_answer=counterfactual_label,
            gold_answer_variants=name_answer_variants(counterfactual_label),
            question_type="counterfactual",
        ),
    ]
    return QuestionBundle(
        main_question=main,
        gold_answer=answer_label,
        questions=questions,
        supported_conclusions=[
            f"{answer_label} is the final custodian of the {flavor.token}.",
            f"Changing only the final recipient makes {counterfactual_label} the custodian.",
        ],
        counterfactual=CounterfactualTask(
            question=questions[2].question,
            answer=counterfactual_label,
            intervention=intervention.description,
        ),
        falsifier=FalsifierTask(
            hypothesis=f"{counterfactual_label} held the token in the observed world",
            minimal_evidence=[events[-1].fact_id],
        ),
    )


def _world(
    *,
    recipe: GenerationRecipe,
    names: list[tuple[str, str]],
    answer_id: str,
    counterfactual_id: str,
    family: FamilySpec,
    final_minute: int,
) -> WorldSpec:
    from cogito_mill.pipelines.concept_templates import minutes_to_clock

    return WorldSpec(
        id=f"world-{recipe.seed}",
        entities=[
            Entity(id=person_id, type="person", label=label, aliases=[label.split()[0]])
            for person_id, label in names
        ],
        relations=[],
        time_points=[
            TimePoint(id="t_incident", label=minutes_to_clock(final_minute), order=1),
        ],
        events=[
            Event(
                id="e_incident",
                label=family.incident,
                actor=answer_id,
                time_point="t_incident",
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
            id="iv_final_handoff",
            description="Change only the recipient of the final witnessed handoff.",
            disable_event="e_incident",
            expected_target_value=counterfactual_id,
        ),
        answer_entity=answer_id,
        candidate_answers=[person_id for person_id, _ in names],
    )


def _offline_draft(
    *,
    family: FamilySpec,
    flavor: ProvenanceFlavor,
    visible_facts: list[VisibleFact],
    final_minute: int,
) -> StoryDraft:
    from cogito_mill.pipelines.concept_templates import minutes_to_clock

    opening = (
        f"During {family.incident} in {family.setting}, investigators found that ordinary access "
        f"could not identify one person: every custodian had entered the relevant work area. "
        f"The useful record was the wandering {flavor.token}, kept inside one of three sealed "
        f"containers and witnessed whenever a seam opened or custody changed. At "
        f"{minutes_to_clock(final_minute)}, the {flavor.checkpoint} accepted its unique imprint. "
        "The afternoon therefore had to be reconstructed as a chain of physical custody rather "
        "than a list of possible doorways."
    )
    scenes: list[SceneDraft] = []
    scene_titles = (
        "Opening inspection",
        "First exchanges",
        "The middle of the afternoon",
        "Late custody changes",
        "The authorization record",
    )
    atmosphere = (
        "Receipts, ordinary errands, and the low noise of the gathering continued around the "
        "witnessed seals.",
        "People crossed paths for mundane work, so a familiar face near the room proved very "
        "little by itself.",
        "A public badge and several unsealed papers also changed hands, making object identity "
        "more useful than suspicion.",
        "The later exchanges were remembered because each recipient initialed the same physical "
        "custody line.",
        "By evening, the witnesses agreed on the handoffs even when they disagreed about "
        "motives and gossip.",
    )
    for index in range(1, 6):
        obligations = [
            fact
            for fact in visible_facts
            if fact.scene_id == f"sc{index}" and fact.role == "required"
        ]
        context = [
            fact
            for fact in visible_facts
            if fact.scene_id == f"sc{index}" and fact.role != "required"
        ]
        prose = " ".join([atmosphere[index - 1], *[fact.text for fact in obligations + context]])
        scenes.append(
            SceneDraft(
                id=f"sc{index}",
                title=scene_titles[index - 1],
                obligated_fact_ids=[fact.id for fact in obligations],
                prose=prose,
            )
        )
    return StoryDraft(
        title=f"The Custody Line at {family.crime_place.title()}",
        opening=opening,
        scenes=scenes,
    )


__all__ = [
    "FLAVORS",
    "MAIN_STEMS",
    "build_provenance_puzzle",
]
