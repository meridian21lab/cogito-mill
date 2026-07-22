"""Timeline/alibi concept portfolio — human-graspable multi-hop deduction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from cogito_mill.domain.appendix import (
    EliminationNote,
    EvidenceIntervention,
    SolverAppendix,
    TimelineSegment,
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
from cogito_mill.domain.recipe import GenerationRecipe, SettingFamily
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


@dataclass(frozen=True)
class FamilySpec:
    id: str
    concept: str
    setting: str
    setting_family: SettingFamily
    incident: str
    crime_place: str
    places: tuple[str, str, str]
    travel: tuple[int, int, int]
    # travel minutes: crime<->a, crime<->b, a<->b


FAMILIES = (
    FamilySpec(
        "festival_theft",
        "jewelry thief",
        "a shopping center hosting a local potato festival",
        SettingFamily.DOMESTIC,
        "the diamond case robbery",
        "jewelry boutique",
        ("festival hall", "gas station", "designer shop"),
        (8, 35, 40),
    ),
    FamilySpec(
        "archive_theft",
        "folio thief",
        "a monastic archive preparing for floodwaters",
        SettingFamily.HISTORICAL,
        "the protected folio's disappearance",
        "scriptorium vault",
        ("courtyard", "gatehouse", "copying room"),
        (5, 12, 10),
    ),
    FamilySpec(
        "habitat_sabotage",
        "cooling saboteur",
        "an orbital habitat fighting a cascading cooling fault",
        SettingFamily.SPECULATIVE,
        "the isolation command that sealed ring three",
        "command niche",
        ("service corridor", "airlock foyer", "diagnostic bay"),
        (6, 15, 12),
    ),
    FamilySpec(
        "museum_release",
        "unauthorized releaser",
        "a city museum evacuating its collection during a blackout",
        SettingFamily.WORKPLACE,
        "the unlawful release of the sealed collection",
        "sealed gallery",
        ("loading bay", "records office", "front lobby"),
        (7, 10, 9),
    ),
    FamilySpec(
        "convoy_diversion",
        "signal hijacker",
        "a desert expedition racing to decode emergency beacons",
        SettingFamily.EXPEDITION,
        "the false transmission that diverted the rescue convoy",
        "relay tent",
        ("supply cache", "mess hall", "beacon ridge"),
        (10, 20, 15),
    ),
    FamilySpec(
        "workshop_switch",
        "artifact thief",
        "a conservation workshop tracing a damaged ceremonial object",
        SettingFamily.WORKPLACE,
        "the substitution of the gilded dial",
        "treatment room",
        ("anteroom", "chemical stores", "front desk"),
        (4, 8, 6),
    ),
)

MAIN_STEMS = (
    "Who carried out {incident}? Give the full name.",
    "Only one person had the opportunity for {incident}. Who was it? Give the full name.",
    "From the timeline, who alone could have done {incident}? Give the full name.",
    "Which full name belongs to the person who robbed the opportunity window for {incident}?",
    "Reconstruct the afternoon. Who is forced to be responsible for {incident}? Give the full name.",
    "Who remains after every alibi and travel constraint is applied for {incident}? Give the full name.",
    "Name the only person who could still have been present for {incident}. Give the full name.",
    "Which full name survives elimination for {incident}?",
    "Using times and travel only, who must have done {incident}? Give the full name.",
    "Who is the sole remaining candidate for {incident}? Give the full name.",
    "After placing every alibi, who is left for {incident}? Give the full name.",
    "Which person alone fits the opportunity window for {incident}? Give the full name.",
)


@dataclass
class Segment:
    place: str
    start: int
    end: int
    summary: str
    fact_id: str = ""


@dataclass
class PersonTimeline:
    person_id: str
    label: str
    segments: list[Segment] = field(default_factory=list)


@dataclass
class ConceptPuzzle:
    family_id: str
    world: WorldSpec
    visible: VisibleTheory
    questions: QuestionBundle
    offline_draft: StoryDraft
    n_hops: int
    appendix: SolverAppendix
    setting_family: SettingFamily


def family_for_seed(seed: int) -> FamilySpec:
    return FAMILIES[seed % len(FAMILIES)]


def _first_name(label: str) -> str:
    return label.split()[0]


def _surname(label: str) -> str:
    parts = label.split()
    return parts[-1] if len(parts) > 1 else parts[0]


def minutes_to_clock(minute: int) -> str:
    hour, mins = divmod(minute, 60)
    hour12 = hour % 12 or 12
    suffix = "AM" if hour < 12 else "PM"
    return f"{hour12}:{mins:02d} {suffix}"


def travel_matrix(family: FamilySpec) -> dict[str, dict[str, int]]:
    crime, a, b, c = family.crime_place, *family.places
    ab, ac, bc = family.travel
    # Map places: a=places[0], b=places[1], c=places[2]
    # travel tuple: crime<->a, crime<->b, a<->b — extend for c
    matrix = {
        crime: {crime: 0, a: ab, b: ac, c: ab + 3},
        a: {crime: ab, a: 0, b: bc, c: bc + 2},
        b: {crime: ac, a: bc, b: 0, c: 5},
        c: {crime: ab + 3, a: bc + 2, b: 5, c: 0},
    }
    return matrix


def has_opportunity(
    segments: list[Segment],
    *,
    crime_place: str,
    crime_start: int,
    crime_end: int,
    travel: dict[str, dict[str, int]],
) -> bool:
    """True iff the person could have been at the crime place for the whole window."""
    ordered = sorted(segments, key=lambda item: item.start)
    for segment in ordered:
        if segment.place == crime_place:
            continue
        if segment.start < crime_end and segment.end > crime_start:
            return False

    prior = [segment for segment in ordered if segment.end <= crime_start]
    if prior:
        last = prior[-1]
        if last.end + travel[last.place][crime_place] > crime_start:
            return False

    later = [segment for segment in ordered if segment.start >= crime_end]
    if later:
        nxt = later[0]
        if crime_end + travel[crime_place][nxt.place] > nxt.start:
            return False
    return True


def elimination_reason(
    segments: list[Segment],
    *,
    crime_place: str,
    crime_start: int,
    crime_end: int,
    travel: dict[str, dict[str, int]],
) -> tuple[str, list[str]]:
    ordered = sorted(segments, key=lambda item: item.start)
    for segment in ordered:
        if segment.place == crime_place:
            continue
        if segment.start < crime_end and segment.end > crime_start:
            return (
                (
                    f"seen at {segment.place} from {minutes_to_clock(segment.start)} to "
                    f"{minutes_to_clock(segment.end)}, overlapping the incident"
                ),
                [segment.fact_id],
            )
    prior = [segment for segment in ordered if segment.end <= crime_start]
    if prior:
        last = prior[-1]
        need = travel[last.place][crime_place]
        if last.end + need > crime_start:
            return (
                (
                    f"left {last.place} at {minutes_to_clock(last.end)}; "
                    f"{need} minutes of travel cannot reach {crime_place} by "
                    f"{minutes_to_clock(crime_start)}"
                ),
                [last.fact_id],
            )
    later = [segment for segment in ordered if segment.start >= crime_end]
    if later:
        nxt = later[0]
        need = travel[crime_place][nxt.place]
        if crime_end + need > nxt.start:
            return (
                (
                    f"must be at {nxt.place} by {minutes_to_clock(nxt.start)}; "
                    f"{need} minutes from {crime_place} after {minutes_to_clock(crime_end)} "
                    "is impossible"
                ),
                [nxt.fact_id],
            )
    return ("no blocking constraint", [])


def build_concept_puzzle(recipe: GenerationRecipe) -> ConceptPuzzle:
    """Build one timeline/alibi mystery with a unique opportunity answer."""
    family = family_for_seed(recipe.seed)
    names = _names(recipe.seed, recipe.n_suspects)
    answer_idx = _pick(recipe.seed, "answer", len(names))
    runner_idx = (answer_idx + 1 + _pick(recipe.seed, "runner", len(names) - 1)) % len(names)
    if runner_idx == answer_idx:
        runner_idx = (runner_idx + 1) % len(names)

    crime_start = 14 * 60 + 30 + (recipe.seed % 4) * 5  # 14:30–14:45
    crime_end = crime_start + 20 + (recipe.seed % 3) * 5  # 20–30 minute window
    travel = travel_matrix(family)
    timelines = _build_timelines(
        recipe.seed,
        family,
        names,
        answer_idx=answer_idx,
        runner_idx=runner_idx,
        crime_start=crime_start,
        crime_end=crime_end,
        travel=travel,
    )

    answer_id, answer_label = names[answer_idx]
    runner_id, runner_label = names[runner_idx]
    assert has_opportunity(
        timelines[answer_id].segments,
        crime_place=family.crime_place,
        crime_start=crime_start,
        crime_end=crime_end,
        travel=travel,
    )
    for person_id, timeline in timelines.items():
        if person_id == answer_id:
            continue
        assert not has_opportunity(
            timeline.segments,
            crime_place=family.crime_place,
            crime_start=crime_start,
            crime_end=crime_end,
            travel=travel,
        )

    visible_facts, logic_facts, rules = _facts_and_logic(
        family=family,
        timelines=timelines,
        answer_id=answer_id,
        crime_start=crime_start,
        crime_end=crime_end,
        travel=travel,
        seed=recipe.seed,
    )
    intervention = _find_evidence_intervention(
        family=family,
        timelines=timelines,
        answer_id=answer_id,
        runner_id=runner_id,
        crime_start=crime_start,
        crime_end=crime_end,
        travel=travel,
    )
    questions = _questions(
        recipe,
        family,
        answer_label,
        runner_label,
        timelines,
        crime_start,
        crime_end,
        intervention,
    )
    eliminations: list[EliminationNote] = []
    for person_id, timeline in timelines.items():
        if person_id == answer_id:
            continue
        reason, fact_ids = elimination_reason(
            timeline.segments,
            crime_place=family.crime_place,
            crime_start=crime_start,
            crime_end=crime_end,
            travel=travel,
        )
        eliminations.append(
            EliminationNote(
                person_label=timeline.label,
                reason=reason,
                fact_ids=fact_ids,
            )
        )
    falsifier = FalsifierTask(
        hypothesis=f"{runner_label} had opportunity for {family.incident}",
        minimal_evidence=[
            "f_crime_window",
            *intervention.fact_ids(),
            *[note.fact_ids[0] for note in eliminations if note.fact_ids][:2],
        ],
    )
    questions = questions.model_copy(update={"falsifier": falsifier})
    appendix = _build_appendix(
        recipe=recipe,
        family=family,
        timelines=timelines,
        travel=travel,
        crime_start=crime_start,
        crime_end=crime_end,
        answer_id=answer_id,
        eliminations=eliminations,
        intervention=intervention,
        falsifier=falsifier,
        supported_conclusions=questions.supported_conclusions,
    )
    world = _world(recipe, names, answer_id, family, intervention, crime_start)
    draft = _offline_draft(recipe, family, visible_facts, crime_start, crime_end)
    # Hops: crime facts + travel facts + per-person segment checks + elimination summary.
    n_hops = 3 + len(travel) + sum(len(item.segments) for item in timelines.values())
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=VisibleTheory(
            id=f"vis-{recipe.seed}",
            world_id=f"world-{recipe.seed}",
            facts=visible_facts,
            logic=LogicTheory(facts=logic_facts, rules=rules),
        ),
        questions=questions,
        offline_draft=draft,
        n_hops=n_hops,
        appendix=appendix,
        setting_family=family.setting_family,
    )


def _build_timelines(
    seed: int,
    family: FamilySpec,
    names: list[tuple[str, str]],
    *,
    answer_idx: int,
    runner_idx: int,
    crime_start: int,
    crime_end: int,
    travel: dict[str, dict[str, int]],
) -> dict[str, PersonTimeline]:
    crime = family.crime_place
    place_a, place_b, place_c = family.places
    timelines: dict[str, PersonTimeline] = {}

    for idx, (person_id, label) in enumerate(names):
        first = _first_name(label)
        if idx == answer_idx:
            # Free during crime; nearby earlier and elsewhere later with enough travel slack.
            pre_end = crime_start - travel[place_a][crime] - 5
            post_start = crime_end + travel[crime][place_c] + 5
            segments = [
                Segment(
                    place_a,
                    pre_end - 40,
                    pre_end,
                    (
                        f"{first} spent time at the {place_a} until "
                        f"{minutes_to_clock(pre_end)}, then moved on."
                    ),
                ),
                Segment(
                    place_c,
                    post_start,
                    post_start + 25,
                    (
                        f"{first} was noticed at the {place_c} from "
                        f"{minutes_to_clock(post_start)} onward."
                    ),
                ),
            ]
        elif idx == runner_idx:
            # Blocked: appears far away shortly after crime start (can't have stayed for window).
            arrive_elsewhere = crime_start + 10
            leave_prior = arrive_elsewhere - travel[crime][place_b]
            # Prior segment at crime-adjacent place ends too late to commit full window
            # and still reach place_b.
            segments = [
                Segment(
                    place_a,
                    crime_start - 50,
                    leave_prior,
                    (f"{first} left the {place_a} around {minutes_to_clock(leave_prior)}."),
                ),
                Segment(
                    place_b,
                    arrive_elsewhere,
                    arrive_elsewhere + 20,
                    (f"{first} was seen at the {place_b} at {minutes_to_clock(arrive_elsewhere)}."),
                ),
            ]
        else:
            pattern = (idx + seed) % 3
            if pattern == 0:
                # Direct overlap alibi at another place during crime.
                segments = [
                    Segment(
                        place_c,
                        crime_start - 10,
                        crime_end + 5,
                        (
                            f"{first} remained at the {place_c} through "
                            f"{minutes_to_clock(crime_start)}–{minutes_to_clock(crime_end)}."
                        ),
                    )
                ]
            elif pattern == 1:
                # Cannot arrive in time from far place.
                leave = crime_start - travel[place_b][crime] + 5
                segments = [
                    Segment(
                        place_b,
                        leave - 35,
                        leave,
                        (f"{first} was still at the {place_b} at {minutes_to_clock(leave)}."),
                    )
                ]
            else:
                # Cannot make next appointment after crime.
                nxt = crime_end + travel[crime][place_a] - 5
                segments = [
                    Segment(
                        place_a,
                        nxt,
                        nxt + 30,
                        (f"{first} had to be at the {place_a} by {minutes_to_clock(nxt)}."),
                    )
                ]
        for seg_i, segment in enumerate(segments):
            segment.fact_id = f"f_seg_{person_id}_{seg_i}"
        timelines[person_id] = PersonTimeline(person_id, label, segments)

    # Verify construction; repair runner/others if needed by extending blocks.
    for person_id, timeline in list(timelines.items()):
        ok = has_opportunity(
            timeline.segments,
            crime_place=crime,
            crime_start=crime_start,
            crime_end=crime_end,
            travel=travel,
        )
        if person_id == names[answer_idx][0]:
            if not ok:
                raise ValueError("answer lacks opportunity")
        elif ok:
            # Force an overlapping alibi.
            first = _first_name(timeline.label)
            timeline.segments.append(
                Segment(
                    place_c,
                    crime_start,
                    crime_end,
                    (
                        f"{first} was accounted for at the {place_c} during "
                        f"{minutes_to_clock(crime_start)}–{minutes_to_clock(crime_end)}."
                    ),
                    fact_id=f"f_seg_{person_id}_block",
                )
            )
    return timelines


def _facts_and_logic(
    *,
    family: FamilySpec,
    timelines: dict[str, PersonTimeline],
    answer_id: str,
    crime_start: int,
    crime_end: int,
    travel: dict[str, dict[str, int]],
    seed: int,
) -> tuple[list[VisibleFact], list[LogicAtom], list[LogicRule]]:
    facts: list[VisibleFact] = []
    logic_facts: list[LogicAtom] = []
    rules: list[LogicRule] = []
    order = 1

    crime_atom = LogicAtom(
        predicate="crime_window",
        arguments=[family.crime_place, str(crime_start), str(crime_end)],
    )
    logic_facts.append(crime_atom)
    facts.append(
        VisibleFact(
            id="f_crime_window",
            text=(
                f"{family.incident.capitalize()} happened at the {family.crime_place} "
                f"between {minutes_to_clock(crime_start)} and {minutes_to_clock(crime_end)}. "
                "Whoever did it had to remain there for that whole stretch."
            ),
            formal=f"atom:{crime_atom.key}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=order,
        )
    )
    order += 1

    # Travel facts as narrative sentences, not a table.
    place_pairs = [
        (family.crime_place, family.places[0]),
        (family.crime_place, family.places[1]),
        (family.crime_place, family.places[2]),
        (family.places[0], family.places[1]),
        (family.places[0], family.places[2]),
    ]
    travel_frames = (
        "Getting from the {origin} to the {dest} usually took about {minutes} minutes that afternoon.",
        "Anyone walking from the {origin} to the {dest} needed about {minutes} minutes.",
        "The short trip between the {origin} and the {dest} was about {minutes} minutes in festival traffic.",
        "From the {origin} over to the {dest} was roughly a {minutes}-minute journey.",
    )
    for pair_i, (origin, dest) in enumerate(place_pairs):
        minutes = travel[origin][dest]
        atom = LogicAtom(predicate="travel", arguments=[origin, dest, str(minutes)])
        logic_facts.append(atom)
        frame = travel_frames[(seed + pair_i) % len(travel_frames)]
        facts.append(
            VisibleFact(
                id=f"f_travel_{_slug(origin)}_{_slug(dest)}",
                text=frame.format(origin=origin, dest=dest, minutes=minutes),
                formal=f"atom:{atom.key}",
                channel=ClueChannel.RECORD,
                role="required",
                scene_id="sc1",
                reveal_order=order,
            )
        )
        order += 1

    # Surname disclosures without contiguous full-name strings.
    for person_id, timeline in timelines.items():
        first = _first_name(timeline.label)
        last = _surname(timeline.label)
        facts.append(
            VisibleFact(
                id=f"f_surname_{person_id}",
                text=f"Staff notes give {first} the surname {last}.",
                formal=f"name:{person_id}",
                channel=ClueChannel.RECORD,
                role="required",
                scene_id="sc2",
                reveal_order=order,
            )
        )
        order += 1

    # Noise / atmosphere distractors.
    noise = [
        (
            f"f_noise_{seed % 7}",
            (
                f"Earlier in the day, crowds drifted through {family.setting}, "
                "and several people looked briefly suspicious for unrelated reasons."
            ),
        ),
        (
            f"f_noise_b_{seed % 5}",
            (
                "Witnesses argued about coats and bags, but none of those details fixed "
                "anyone at the critical doorway during the incident window."
            ),
        ),
    ]
    for fact_id, text in noise:
        facts.append(
            VisibleFact(
                id=fact_id,
                text=text,
                formal=f"noise:{fact_id}",
                channel=ClueChannel.STATEMENT,
                role="distractor",
                scene_id="sc2",
                reveal_order=order,
            )
        )
        order += 1

    scene_cycle = ["sc2", "sc3", "sc4", "sc5"]
    scene_i = 0
    for timeline in timelines.values():
        for segment in timeline.segments:
            atom = LogicAtom(
                predicate="seen_at",
                arguments=[
                    timeline.person_id,
                    segment.place,
                    str(segment.start),
                    str(segment.end),
                ],
            )
            logic_facts.append(atom)
            facts.append(
                VisibleFact(
                    id=segment.fact_id,
                    text=segment.summary,
                    formal=f"atom:{atom.key}",
                    channel=ClueChannel.STATEMENT,
                    role="required",
                    scene_id=scene_cycle[scene_i % len(scene_cycle)],
                    reveal_order=order,
                )
            )
            order += 1
            scene_i += 1

    # Opportunity atoms only for the answer; blocked atoms for others.
    for person_id, timeline in timelines.items():
        if person_id == answer_id:
            atom = LogicAtom(predicate="has_opportunity", arguments=[person_id])
            logic_facts.append(atom)
            rule = LogicRule(
                id=f"opportunity_{person_id}",
                premises=[
                    LogicAtom(
                        predicate="seen_at",
                        arguments=[person_id, seg.place, str(seg.start), str(seg.end)],
                    )
                    for seg in timeline.segments
                ]
                + [crime_atom],
                conclusion=atom,
                explanation=(
                    f"{timeline.label} is free of blocking alibis and can reach the "
                    f"{family.crime_place} for the full incident window."
                ),
            )
            rules.append(rule)
        else:
            atom = LogicAtom(predicate="blocked", arguments=[person_id])
            logic_facts.append(atom)

    final_rule = LogicRule(
        id=f"final_{family.id}",
        premises=[LogicAtom(predicate="has_opportunity", arguments=["?person"])],
        conclusion=LogicAtom(predicate="qualifies", arguments=["?person"]),
        explanation="Only a person with uninterrupted opportunity qualifies.",
    )
    rules.append(final_rule)
    facts.append(
        VisibleFact(
            id="f_rule_opportunity",
            text=(
                "Whoever did it had to remain at the scene for the whole stretch of the "
                "incident window. Sightings and travel times are the only fair tests."
            ),
            formal=f"rule:{final_rule.id}",
            channel=ClueChannel.RULE_APPLICATION,
            role="required",
            scene_id="sc5",
            reveal_order=order,
        )
    )
    return facts, logic_facts, rules


def _find_evidence_intervention(
    *,
    family: FamilySpec,
    timelines: dict[str, PersonTimeline],
    answer_id: str,
    runner_id: str,
    crime_start: int,
    crime_end: int,
    travel: dict[str, dict[str, int]],
) -> EvidenceIntervention:
    """Two-fact edit: free the runner and block the answer."""
    answer = timelines[answer_id]
    runner = timelines[runner_id]
    # Block answer with an overlapping alibi; free runner by removing far sighting.
    answer_block = Segment(
        family.places[2],
        crime_start,
        crime_end,
        (
            f"{answer.label} remained at the {family.places[2]} from "
            f"{minutes_to_clock(crime_start)} to {minutes_to_clock(crime_end)}."
        ),
        fact_id=answer.segments[0].fact_id,
    )
    # Runner becomes free if their blocking segment is replaced by a pre-crime nearby visit.
    runner_free = Segment(
        family.places[0],
        crime_start - travel[family.places[0]][family.crime_place] - 30,
        crime_start - travel[family.places[0]][family.crime_place] - 5,
        (
            f"{runner.label} left the {family.places[0]} early enough to reach the "
            f"{family.crime_place} before {minutes_to_clock(crime_start)}."
        ),
        fact_id=runner.segments[-1].fact_id,
    )
    trial_answer = [
        answer_block if seg.fact_id == answer_block.fact_id else seg for seg in answer.segments
    ]
    if all(seg.fact_id != answer_block.fact_id for seg in trial_answer):
        trial_answer = [*answer.segments, answer_block]
    trial_runner = [
        runner_free if seg.fact_id == runner_free.fact_id else seg for seg in runner.segments
    ]
    # Prefer editing the runner's last segment description in the question.
    return EvidenceIntervention(
        person_id=runner_id,
        person_label=runner.label,
        fact_id=runner.segments[-1].fact_id,
        description=(
            f"{runner.label}'s later sighting had instead placed them at the "
            f"{family.places[0]} until only "
            f"{minutes_to_clock(runner_free.end)}, with no later far-away sighting"
        ),
        answer_label=runner.label,
        secondary_person_id=answer_id,
        secondary_person_label=answer.label,
        secondary_fact_id=answer.segments[0].fact_id,
        secondary_description=(
            f"{answer.label} had been seen at the {family.places[2]} throughout "
            f"{minutes_to_clock(crime_start)}–{minutes_to_clock(crime_end)}"
        ),
    )


def _questions(
    recipe: GenerationRecipe,
    family: FamilySpec,
    answer: str,
    runner: str,
    timelines: dict[str, PersonTimeline],
    crime_start: int,
    crime_end: int,
    intervention: EvidenceIntervention,
) -> QuestionBundle:
    main = MAIN_STEMS[_pick(recipe.seed, "stem", len(MAIN_STEMS))].format(incident=family.incident)
    runner_timeline = next(item for item in timelines.values() if item.label == runner)
    probe = runner_timeline.segments[-1]
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
                f"Where was {runner} at {minutes_to_clock(probe.start)}? "
                "Answer with the place name only."
            ),
            gold_answer=probe.place,
            gold_answer_variants=[probe.place],
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If {intervention.question_clause()}, while every other sighting stayed fixed, "
                f"who would be responsible for {family.incident}? "
                "Give the full name, or answer exactly none."
            ),
            gold_answer=intervention.answer_label,
            gold_answer_variants=(
                ["none"]
                if intervention.answer_label == "none"
                else name_answer_variants(intervention.answer_label)
            ),
            question_type="counterfactual",
        ),
        ScoredQuestion(
            id="q_time",
            question="At what clock time did the incident window begin? Answer in h:mm AM/PM format.",
            gold_answer=minutes_to_clock(crime_start),
            gold_answer_variants=[
                minutes_to_clock(crime_start),
                minutes_to_clock(crime_start).lower(),
            ],
            question_type="scalar",
        ),
    ]
    return QuestionBundle(
        main_question=main,
        gold_answer=answer,
        questions=questions,
        supported_conclusions=[
            f"{answer} alone had opportunity during {minutes_to_clock(crime_start)}–"
            f"{minutes_to_clock(crime_end)}.",
            f"After the evidence edit, the result is {intervention.answer_label}.",
        ],
        counterfactual=CounterfactualTask(
            question=questions[2].question,
            answer=intervention.answer_label,
            intervention=intervention.question_clause(),
        ),
        falsifier=FalsifierTask(
            hypothesis=f"{runner} already had opportunity",
            minimal_evidence=["f_crime_window", probe.fact_id],
        ),
    )


def _build_appendix(
    *,
    recipe: GenerationRecipe,
    family: FamilySpec,
    timelines: dict[str, PersonTimeline],
    travel: dict[str, dict[str, int]],
    crime_start: int,
    crime_end: int,
    answer_id: str,
    eliminations: list[EliminationNote],
    intervention: EvidenceIntervention,
    falsifier: FalsifierTask,
    supported_conclusions: list[str],
) -> SolverAppendix:
    timeline_map: dict[str, list[TimelineSegment]] = {}
    opportunity: dict[str, bool] = {}
    for person_id, timeline in timelines.items():
        timeline_map[timeline.label] = [
            TimelineSegment(
                place=segment.place,
                start_minute=segment.start,
                end_minute=segment.end,
                fact_id=segment.fact_id,
                summary=segment.summary,
            )
            for segment in timeline.segments
        ]
        opportunity[timeline.label] = person_id == answer_id
    return SolverAppendix(
        id=f"lss-concept-{recipe.seed:06d}",
        mechanism="timeline_opportunity",
        incident={
            "family": family.id,
            "incident": family.incident,
            "place": family.crime_place,
            "start": minutes_to_clock(crime_start),
            "end": minutes_to_clock(crime_end),
            "start_minute": crime_start,
            "end_minute": crime_end,
        },
        travel_minutes=travel,
        timelines=timeline_map,
        opportunity=opportunity,
        eliminations=eliminations,
        supported_conclusions=supported_conclusions,
        evidence_counterfactual=intervention,
        falsifier=falsifier,
        notes=[
            "Thin Hub items stay story-only; this appendix is a companion audit artifact.",
            "Deduction is temporal opportunity under travel constraints, not arithmetic tallies.",
        ],
    )


def _world(
    recipe: GenerationRecipe,
    names: list[tuple[str, str]],
    answer_id: str,
    family: FamilySpec,
    intervention: EvidenceIntervention,
    crime_start: int,
) -> WorldSpec:
    return WorldSpec(
        id=f"world-{recipe.seed}",
        entities=[
            Entity(id=person_id, type="person", label=label, aliases=[label.split()[0]])
            for person_id, label in names
        ],
        relations=[],
        time_points=[
            TimePoint(id="t_crime", label=minutes_to_clock(crime_start), order=1),
        ],
        events=[
            Event(
                id="e_incident",
                label=family.incident,
                actor=answer_id,
                time_point="t_crime",
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
            id="iv_timeline_edit",
            description=intervention.question_clause(),
            disable_event="e_incident",
            expected_target_value="none",
        ),
        answer_entity=answer_id,
        candidate_answers=[person_id for person_id, _ in names],
    )


def _offline_draft(
    recipe: GenerationRecipe,
    family: FamilySpec,
    facts: list[VisibleFact],
    crime_start: int,
    crime_end: int,
) -> StoryDraft:
    """Build a human-readable scaffold: incident spine, then sightings, then noise."""
    start = minutes_to_clock(crime_start)
    end = minutes_to_clock(crime_end)
    hooks = (
        "a security guard's notebook",
        "a stall vendor's recollection",
        "a shift supervisor's radio log",
        "two independent witness statements",
        "a hurried report from the front desk",
        "a late interview with a delivery driver",
        "an unsigned tip left at reception",
        "a camera tech's incomplete timestamp sheet",
        "a courier's handwritten route card",
        "a kitchen helper's break-time story",
        "an usher's door checklist",
        "a maintenance worker's badge trail",
    )
    hook = hooks[_pick(recipe.seed, "opening-hook", len(hooks))]
    frames = (
        (
            f"From {hook}, the day at {family.setting} snapped into sequence. "
            f"{family.incident.capitalize()} happened at the {family.crime_place} "
            f"between {start} and {end}."
        ),
        (
            f"{hook.capitalize()} was enough to restart the inquiry at {family.setting}. "
            f"The fixed window for {family.incident} at the {family.crime_place} ran "
            f"from {start} to {end}."
        ),
        (
            f"Nobody trusted rumor alone at {family.setting}, so they started with {hook}. "
            f"It placed {family.incident} at the {family.crime_place} between {start} "
            f"and {end}."
        ),
        (
            f"The first usable lead at {family.setting} came from {hook}. "
            f"By then it was clear that {family.incident} had taken the "
            f"{family.crime_place} from {start} through {end}."
        ),
    )
    opening = frames[_pick(recipe.seed, "opening-frame", len(frames))]

    required = sorted(
        (fact for fact in facts if fact.role == "required"),
        key=lambda item: item.reveal_order,
    )
    distractors = sorted(
        (fact for fact in facts if fact.role == "distractor"),
        key=lambda item: item.reveal_order,
    )
    spine = [fact for fact in required if fact.id.startswith(("f_crime", "f_travel"))]
    people = [fact for fact in required if fact.id.startswith("f_seg_")]
    rule = [fact for fact in required if fact.id.startswith("f_rule")]
    other = [
        fact for fact in required if fact not in spine and fact not in people and fact not in rule
    ]

    early = people[: max(1, len(people) // 3)]
    middle = people[max(1, len(people) // 3) : max(2, 2 * len(people) // 3)]
    late = people[max(2, 2 * len(people) // 3) :]

    scene_groups: list[tuple[str, str, list[VisibleFact], str]] = [
        (
            "sc1",
            "The incident window",
            spine,
            (
                "First the fixed points. "
                + " ".join(fact.text for fact in spine)
                + " Anyone reconstructing the afternoon needed those travel times as much "
                "as any witness name."
            ),
        ),
        (
            "sc2",
            "Early movements",
            early + other,
            (
                "Earlier in the afternoon, ordinary errands and appointments began to "
                "cross. " + " ".join(fact.text for fact in early + other)
            ),
        ),
        (
            "sc3",
            "Around the window",
            middle,
            (
                "Closer to the critical hour, the map of who was where tightened. "
                + " ".join(fact.text for fact in middle)
            ),
        ),
        (
            "sc4",
            "Noise and side details",
            distractors + late,
            (
                "Not every observation mattered, but the day was full of them. "
                + " ".join(fact.text for fact in distractors + late)
            ),
        ),
        (
            "sc5",
            "What the timeline forces",
            rule,
            (
                "By evening the clocks and routes were all on the table. "
                + " ".join(fact.text for fact in rule)
                + " The rest was ordinary reconstruction: who could still fit the window."
            ),
        ),
    ]
    scenes = [
        SceneDraft(
            id=scene_id,
            title=title,
            obligated_fact_ids=[fact.id for fact in group],
            prose=prose.strip(),
        )
        for scene_id, title, group, prose in scene_groups
    ]
    return StoryDraft(
        title=f"{family.concept.title()} — Case {recipe.seed}",
        opening=opening,
        scenes=scenes,
    )


def _names(seed: int, n: int) -> list[tuple[str, str]]:
    pairs = [(first, last) for first in FIRST for last in LAST]
    ordered = sorted(
        pairs,
        key=lambda pair: hashlib.sha256(
            f"{seed}:timeline-name:{pair[0]}:{pair[1]}".encode()
        ).digest(),
    )
    selected: list[tuple[str, str]] = []
    seen_first: set[str] = set()
    seen_last: set[str] = set()
    for first, last in ordered:
        if first in seen_first or last in seen_last:
            continue
        seen_first.add(first)
        seen_last.add(last)
        selected.append((first, last))
        if len(selected) >= n:
            break
    if len(selected) < n:
        raise ValueError(f"need {n} unique given/surname pairs but only {len(selected)} available")
    return [(f"p{i}", f"{first} {last}") for i, (first, last) in enumerate(selected)]


def _pick(seed: int, salt: str, modulo: int) -> int:
    return hashlib.sha256(f"{seed}:{salt}".encode()).digest()[0] % modulo


def _slug(text: str) -> str:
    return re_sub(text)


def re_sub(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_")


build_timeline_puzzle = build_concept_puzzle


def build_concept_puzzle(recipe: GenerationRecipe) -> ConceptPuzzle:
    """Dispatch to the versioned structural mechanism without changing Hub schemas."""
    if recipe.prompt_version == "pilot.v5":
        from cogito_mill.pipelines.provenance_templates import build_provenance_puzzle

        return build_provenance_puzzle(recipe)
    return build_timeline_puzzle(recipe)


__all__ = [
    "ConceptPuzzle",
    "FAMILIES",
    "build_concept_puzzle",
    "build_timeline_puzzle",
    "family_for_seed",
    "has_opportunity",
    "minutes_to_clock",
]
