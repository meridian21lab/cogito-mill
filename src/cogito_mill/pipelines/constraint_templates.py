"""Narrative relational constraint worlds with Z3-verified unique targets."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cogito_mill.domain.appendix import SolverAppendix
from cogito_mill.domain.constraints import ConstraintClue, ConstraintTheory
from cogito_mill.domain.evidence import ClueChannel, VisibleFact, VisibleTheory
from cogito_mill.domain.narrative import SceneDraft, StoryDraft
from cogito_mill.domain.questions import FalsifierTask, QuestionBundle, ScoredQuestion
from cogito_mill.domain.recipe import GenerationRecipe
from cogito_mill.domain.world import Entity, Event, TargetClaim, TimePoint, WorldSpec
from cogito_mill.eval.score import name_answer_variants
from cogito_mill.reasoning.constraints import target_candidates

if TYPE_CHECKING:
    from cogito_mill.pipelines.concept_templates import ConceptPuzzle, FamilySpec


@dataclass(frozen=True)
class ConstraintFlavor:
    objects: tuple[str, str, str, str, str, str]
    places: tuple[str, str, str, str, str, str]
    inquiry: str


FLAVORS: dict[str, ConstraintFlavor] = {
    "festival_theft": ConstraintFlavor(
        objects=(
            "diamond release seal",
            "raffle ledger",
            "vendor key",
            "maintenance tag",
            "cash pouch",
            "display card",
        ),
        places=(
            "jewelry boutique",
            "festival office",
            "loading corridor",
            "tasting hall",
            "gas-station kiosk",
            "designer shop",
        ),
        inquiry="the final festival checkpoint",
    ),
    "archive_theft": ConstraintFlavor(
        objects=(
            "bronze archive seal",
            "river charter",
            "gate key",
            "lamp ledger",
            "copyist's folio",
            "wax tablet",
        ),
        places=(
            "scriptorium",
            "gatehouse",
            "upper archive",
            "courtyard",
            "copying room",
            "bell tower",
        ),
        inquiry="the flood-preparation inspection",
    ),
    "habitat_sabotage": ConstraintFlavor(
        objects=(
            "ceramic command wafer",
            "coolant key",
            "repair slate",
            "airlock token",
            "sensor cassette",
            "meal voucher",
        ),
        places=(
            "command niche",
            "diagnostic bay",
            "service corridor",
            "airlock foyer",
            "machine shop",
            "greenhouse lift",
        ),
        inquiry="the ring-three command audit",
    ),
    "museum_release": ConstraintFlavor(
        objects=(
            "numbered gallery key",
            "registrar wallet",
            "bronze label",
            "truck manifest",
            "flashlight case",
            "packing seal",
        ),
        places=(
            "sealed gallery",
            "loading bay",
            "records office",
            "front lobby",
            "registrar room",
            "emergency store",
        ),
        inquiry="the blackout release audit",
    ),
    "convoy_diversion": ConstraintFlavor(
        objects=(
            "brass relay cipher",
            "beacon map",
            "water manifest",
            "radio key",
            "survey slate",
            "fuel docket",
        ),
        places=(
            "relay tent",
            "supply cache",
            "mess shelter",
            "beacon ridge",
            "survey camp",
            "canyon junction",
        ),
        inquiry="the emergency transmission review",
    ),
    "workshop_switch": ConstraintFlavor(
        objects=(
            "engraved treatment seal",
            "gilded dial",
            "solvent key",
            "condition report",
            "pigment case",
            "receipt wallet",
        ),
        places=(
            "treatment room",
            "anteroom",
            "chemical stores",
            "front desk",
            "drying cabinet",
            "loading bench",
        ),
        inquiry="the conservation closeout",
    ),
}

MAIN_STEMS = (
    "Which person handled the {target} during {inquiry}? Give the full name.",
    "Reconcile the witness accounts. Who was paired with the {target}? Give the full name.",
    "Whose full name belongs with the {target} in the only consistent reconstruction?",
    "After satisfying every account, who must have carried the {target}? Give the full name.",
    "Which full name is forced for the custodian of the {target}?",
    "The records admit one consistent owner of the {target}. Who is it? Give the full name.",
    "Who was associated with the {target} at their recorded stop? Give the full name.",
    "Solve the linked times and places. Who had the {target}? Give the full name.",
)


def build_constraint_puzzle(recipe: GenerationRecipe) -> ConceptPuzzle:
    """Build one cross-axis constraint world and expose only its natural-language clues."""
    from cogito_mill.pipelines.concept_templates import (
        ConceptPuzzle,
        _first_name,
        _names,
        _pick,
        _surname,
        family_for_seed,
    )

    if recipe.n_suspects != 6:
        raise ValueError("relational constraint worlds require exactly six people")
    family = family_for_seed(recipe.seed)
    flavor = FLAVORS[family.id]
    names = _names(recipe.seed, 6)
    people = [person_id for person_id, _ in names]
    labels = dict(names)
    objects = list(flavor.objects)
    places = list(flavor.places)
    times = [
        f"{hour}:{minute:02d} PM"
        for hour, minute in ((1, 10), (1, 35), (2, 0), (2, 25), (2, 50), (3, 15))
    ]

    object_assignment = dict(
        zip(people, _permutation(objects, recipe.seed, "objects"), strict=True)
    )
    place_assignment = dict(zip(people, _permutation(places, recipe.seed, "places"), strict=True))
    time_assignment = dict(zip(people, _permutation(times, recipe.seed, "times"), strict=True))
    object_owner = {value: person for person, value in object_assignment.items()}
    target_object = objects[_pick(recipe.seed, "constraint-target", len(objects))]
    answer_id = object_owner[target_object]
    answer_label = labels[answer_id]

    pool = _candidate_clues(
        seed=recipe.seed,
        people=people,
        labels=labels,
        objects=objects,
        places=places,
        times=times,
        object_assignment=object_assignment,
        place_assignment=place_assignment,
        time_assignment=time_assignment,
    )
    theory = _minimal_target_theory(
        people=people,
        objects=objects,
        places=places,
        times=times,
        pool=pool,
        target_object=target_object,
        seed=recipe.seed,
    )
    candidates = target_candidates(theory)
    if candidates != [answer_id]:
        raise ValueError(f"constraint target is not unique: {candidates}")
    if not (10 <= len(theory.clues) <= 30):
        raise ValueError(f"constraint core has unsuitable size: {len(theory.clues)}")
    _assert_clue_ablation(theory, answer_id)
    _assert_axis_dependence(theory, answer_id)

    visible_facts: list[VisibleFact] = []
    order = 1
    for index, (person_id, label) in enumerate(names):
        visible_facts.append(
            VisibleFact(
                id=f"f_surname_{person_id}",
                text=(
                    f"The duty roster records {_first_name(label)} under the surname "
                    f"{_surname(label)}."
                ),
                formal=f"name:{person_id}",
                channel=ClueChannel.RECORD,
                role="required",
                scene_id=f"sc{1 + index % 4}",
                reveal_order=order,
            )
        )
        order += 1
    visible_facts.append(
        VisibleFact(
            id="f_bijection_rule",
            text=(
                "Each person handled one different object, visited one different recorded place, "
                "and had one different appointment time; no object, place, or time was reused."
            ),
            formal="constraint:bijective_axes",
            channel=ClueChannel.RULE_APPLICATION,
            role="required",
            scene_id="sc1",
            reveal_order=order,
        )
    )
    order += 1
    selected_clues: list[ConstraintClue] = []
    for index, clue in enumerate(theory.clues):
        scene_id = f"sc{2 + index % 3}"
        selected = clue.model_copy(update={"scene_id": scene_id})
        selected_clues.append(selected)
        visible_facts.append(
            VisibleFact(
                id=selected.id,
                text=selected.text,
                formal=f"constraint:{selected.id}",
                channel=ClueChannel.STATEMENT,
                role="required",
                scene_id=scene_id,
                reveal_order=order,
            )
        )
        order += 1
    theory = theory.model_copy(update={"clues": selected_clues})

    target_place = place_assignment[answer_id]
    target_time = time_assignment[answer_id]
    main = MAIN_STEMS[_pick(recipe.seed, "constraint-stem", len(MAIN_STEMS))].format(
        target=target_object,
        inquiry=flavor.inquiry,
    )
    questions = QuestionBundle(
        main_question=main,
        gold_answer=answer_label,
        questions=[
            ScoredQuestion(
                id="q_main",
                question=main,
                gold_answer=answer_label,
                gold_answer_variants=name_answer_variants(answer_label),
                question_type="main",
            ),
            ScoredQuestion(
                id="q_target_place",
                question=(
                    f"At which recorded place was the {target_object}? "
                    "Answer with the place name only."
                ),
                gold_answer=target_place,
                gold_answer_variants=[target_place],
                question_type="intermediate",
            ),
            ScoredQuestion(
                id="q_target_time",
                question=(
                    f"At what time was the {target_object} recorded? Answer in h:mm PM format only."
                ),
                gold_answer=target_time,
                gold_answer_variants=[target_time, target_time.lower()],
                question_type="scalar",
            ),
        ],
        supported_conclusions=[
            f"{answer_label} handled the {target_object}.",
            f"The {target_object} was at the {target_place} at {target_time}.",
        ],
        falsifier=FalsifierTask(
            hypothesis=(
                f"{labels[people[(people.index(answer_id) + 1) % len(people)]]} "
                f"handled the {target_object}"
            ),
            minimal_evidence=[clue.id for clue in theory.clues[:3]],
        ),
    )
    solution = {
        labels[person_id]: {
            "object": object_assignment[person_id],
            "place": place_assignment[person_id],
            "time": time_assignment[person_id],
        }
        for person_id in people
    }
    appendix = SolverAppendix(
        id=f"lss-concept-{recipe.seed:06d}",
        mechanism="relational_constraint_world",
        incident={
            "family": family.id,
            "incident": family.incident,
            "target_object": target_object,
            "target_clue_ids": [clue.id for clue in theory.clues],
            "axes": ["person", "object", "place", "time"],
        },
        constraint_clues=theory.clues,
        constraint_solution=solution,
        supported_conclusions=questions.supported_conclusions,
        falsifier=questions.falsifier,
        notes=[
            "No visible clue directly links a person to the target object.",
            "Removing any retained clue makes the target owner non-unique.",
            "Dropping object, place, or time constraints makes the target owner non-unique.",
        ],
    )
    world = _world(
        recipe=recipe,
        family=family,
        names=names,
        answer_id=answer_id,
        target_object=target_object,
        target_time=target_time,
    )
    draft = _offline_draft(
        family=family,
        flavor=flavor,
        target_object=target_object,
        visible_facts=visible_facts,
    )
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=VisibleTheory(
            id=f"vis-{recipe.seed}",
            world_id=f"world-{recipe.seed}",
            facts=visible_facts,
            constraints=theory,
        ),
        questions=questions,
        offline_draft=draft,
        n_hops=len(theory.clues) + 1,
        appendix=appendix,
        setting_family=family.setting_family,
    )


def _candidate_clues(
    *,
    seed: int,
    people: list[str],
    labels: dict[str, str],
    objects: list[str],
    places: list[str],
    times: list[str],
    object_assignment: dict[str, str],
    place_assignment: dict[str, str],
    time_assignment: dict[str, str],
) -> list[ConstraintClue]:
    object_owner = {value: person for person, value in object_assignment.items()}
    place_owner = {value: person for person, value in place_assignment.items()}
    pool: list[ConstraintClue] = []

    def add(kind: str, args: list[str], axes: list[str], text: str) -> None:
        clue_id = f"f_constraint_{len(pool) + 1:03d}"
        pool.append(
            ConstraintClue(
                id=clue_id,
                kind=kind,  # type: ignore[arg-type]
                arguments=args,
                axes=axes,  # type: ignore[arg-type]
                text=text,
                scene_id="sc2",
            )
        )

    for person in people:
        first = labels[person].split()[0]
        for place in _wrong_values(places, place_assignment[person], seed, f"{person}:place", 2):
            add(
                "person_not_place",
                [person, place],
                ["person", "place"],
                f"A delivery receipt proves {first} was not at the {place}.",
            )
        for time in _wrong_values(times, time_assignment[person], seed, f"{person}:time", 2):
            add(
                "person_not_time",
                [person, time],
                ["person", "time"],
                f"The clocked interview rules out {time} as {first}'s appointment.",
            )

    for object_name in objects:
        owner = object_owner[object_name]
        actual_place = place_assignment[owner]
        actual_time = time_assignment[owner]
        for place in _wrong_values(places, actual_place, seed, f"{object_name}:place", 2):
            add(
                "object_not_place",
                [object_name, place],
                ["object", "place"],
                f"The witness who described the {object_name} never saw it at the {place}.",
            )
        for time in _wrong_values(times, actual_time, seed, f"{object_name}:time", 2):
            add(
                "object_not_time",
                [object_name, time],
                ["object", "time"],
                f"The {object_name} was already elsewhere in the record at {time}.",
            )

    for place in places:
        owner = place_owner[place]
        actual_time = time_assignment[owner]
        wrong_time = _wrong_values(times, actual_time, seed, f"{place}:time", 1)[0]
        add(
            "place_not_time",
            [place, wrong_time],
            ["place", "time"],
            f"The signed log shows that the {place} was not the {wrong_time} stop.",
        )

    ordered_people = sorted(people, key=lambda person: times.index(time_assignment[person]))
    ordered_objects = [object_assignment[person] for person in ordered_people]
    ordered_places = [place_assignment[person] for person in ordered_people]
    for left, right in zip(ordered_people, ordered_people[1:], strict=False):
        add(
            "person_before_person",
            [left, right],
            ["person", "time"],
            f"{labels[left].split()[0]}'s appointment came before {labels[right].split()[0]}'s.",
        )
    for left, right in zip(ordered_objects, ordered_objects[1:], strict=False):
        add(
            "object_before_object",
            [left, right],
            ["object", "time"],
            f"The {left} appeared in the record before the {right}.",
        )
    for left, right in zip(ordered_places, ordered_places[1:], strict=False):
        add(
            "place_before_place",
            [left, right],
            ["place", "time"],
            f"The stop at the {left} came before the stop at the {right}.",
        )

    for person in people:
        actual_place = place_assignment[person]
        wrong_time = _wrong_values(times, time_assignment[person], seed, f"{person}:xor-time", 1)[0]
        add(
            "person_place_xor_time",
            [person, actual_place, wrong_time],
            ["person", "place", "time"],
            (
                f"The clerk remembered an exclusive choice: {labels[person].split()[0]} was "
                f"either at the {actual_place} or assigned {wrong_time}, but not both."
            ),
        )
    for object_name in objects:
        owner = object_owner[object_name]
        actual_place = place_assignment[owner]
        wrong_time = _wrong_values(
            times, time_assignment[owner], seed, f"{object_name}:xor-time", 1
        )[0]
        add(
            "object_place_xor_time",
            [object_name, actual_place, wrong_time],
            ["object", "place", "time"],
            (
                f"Exactly one report was accurate: the {object_name} was at the {actual_place}, "
                f"or it was logged at {wrong_time}."
            ),
        )
    return pool


def _minimal_target_theory(
    *,
    people: list[str],
    objects: list[str],
    places: list[str],
    times: list[str],
    pool: list[ConstraintClue],
    target_object: str,
    seed: int,
) -> ConstraintTheory:
    ordered = sorted(
        pool,
        key=lambda clue: hashlib.sha256(f"{seed}:minimize:{clue.id}".encode()).digest(),
    )
    selected = list(pool)
    for clue in ordered:
        trial = [item for item in selected if item.id != clue.id]
        theory = ConstraintTheory(
            people=people,
            objects=objects,
            places=places,
            times=times,
            clues=trial,
            target_object=target_object,
        )
        if len(target_candidates(theory)) == 1:
            selected = trial
    return ConstraintTheory(
        people=people,
        objects=objects,
        places=places,
        times=times,
        clues=selected,
        target_object=target_object,
    )


def _assert_clue_ablation(theory: ConstraintTheory, answer_id: str) -> None:
    for clue in theory.clues:
        reduced = theory.model_copy(
            update={"clues": [item for item in theory.clues if item.id != clue.id]}
        )
        if target_candidates(reduced) == [answer_id]:
            raise ValueError(f"constraint clue is not target-necessary: {clue.id}")


def _assert_axis_dependence(theory: ConstraintTheory, answer_id: str) -> None:
    for axis in ("object", "place", "time"):
        reduced = theory.model_copy(
            update={"clues": [clue for clue in theory.clues if axis not in clue.axes]}
        )
        if target_candidates(reduced) == [answer_id]:
            raise ValueError(f"constraint target does not depend on {axis} clues")


def _permutation(values: list[str], seed: int, salt: str) -> list[str]:
    return sorted(
        values,
        key=lambda value: hashlib.sha256(f"{seed}:{salt}:{value}".encode()).digest(),
    )


def _wrong_values(
    values: list[str],
    actual: str,
    seed: int,
    salt: str,
    count: int,
) -> list[str]:
    return _permutation([value for value in values if value != actual], seed, salt)[:count]


def _world(
    *,
    recipe: GenerationRecipe,
    family: FamilySpec,
    names: list[tuple[str, str]],
    answer_id: str,
    target_object: str,
    target_time: str,
) -> WorldSpec:
    return WorldSpec(
        id=f"world-{recipe.seed}",
        entities=[
            Entity(id=person_id, type="person", label=label, aliases=[label.split()[0]])
            for person_id, label in names
        ],
        relations=[],
        time_points=[TimePoint(id="t_target", label=target_time, order=1)],
        events=[
            Event(
                id="e_target",
                label=f"{family.incident}: {target_object}",
                actor=answer_id,
                time_point="t_target",
                effects=["key_action"],
            )
        ],
        facts=[],
        target=TargetClaim(
            predicate="qualifies",
            arguments=["person"],
            expected_value=answer_id,
        ),
        answer_entity=answer_id,
        candidate_answers=[person_id for person_id, _ in names],
    )


def _offline_draft(
    *,
    family: FamilySpec,
    flavor: ConstraintFlavor,
    target_object: str,
    visible_facts: list[VisibleFact],
) -> StoryDraft:
    opening = (
        f"After {family.incident} in {family.setting}, six people gave overlapping accounts of "
        f"objects, places, and appointment times. The inquiry focused on the {target_object}, "
        "but no witness directly paired it with a person. Receipts, calls, and observations had "
        "to be reconciled as one consistent afternoon."
    )
    scenes: list[SceneDraft] = []
    titles = (
        "The inquiry",
        "Witness accounts",
        "Receipts and calls",
        "Crossed recollections",
        "The unresolved record",
    )
    bridges = (
        "The investigator first fixed the rules of the reconstruction.",
        "Ordinary work continued while the first accounts were compared.",
        "Later receipts narrowed several combinations without naming a culprit.",
        "Other witnesses remembered relative order and mutually exclusive details.",
        f"The records were left for reconciliation during {flavor.inquiry}.",
    )
    for index in range(1, 6):
        facts = [fact for fact in visible_facts if fact.scene_id == f"sc{index}"]
        scenes.append(
            SceneDraft(
                id=f"sc{index}",
                title=titles[index - 1],
                obligated_fact_ids=[fact.id for fact in facts if fact.role == "required"],
                prose=" ".join([bridges[index - 1], *[fact.text for fact in facts]]),
            )
        )
    return StoryDraft(
        title=f"The Linked Accounts at {family.crime_place.title()}",
        opening=opening,
        scenes=scenes,
    )


__all__ = ["FLAVORS", "MAIN_STEMS", "build_constraint_puzzle"]
