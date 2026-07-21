"""Template-backed world and story generation for the pilot."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from cogito_mill.domain.evidence import ClueChannel, VisibleFact, VisibleTheory
from cogito_mill.domain.narrative import SceneDraft, Sentence, StoryDocument
from cogito_mill.domain.questions import (
    CounterfactualTask,
    FalsifierTask,
    QuestionBundle,
    ScoredQuestion,
)
from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe, SettingFamily
from cogito_mill.domain.world import (
    Entity,
    Event,
    Intervention,
    Relation,
    RelationKind,
    Rule,
    TargetClaim,
    TimePoint,
    WorldSpec,
)
from cogito_mill.eval.score import name_answer_variants

FIRST = [
    "Avery", "Blair", "Casey", "Drew", "Eden", "Finley", "Gray", "Harper",
    "Indigo", "Jules", "Kai", "Logan", "Morgan", "Noel", "Oakley", "Parker",
    "Quinn", "Reese", "Sawyer", "Tatum", "Val", "Winter", "Yael", "Zion",
]
LAST = [
    "Nguyen", "Patel", "Ortiz", "Brooks", "Hassan", "Silva", "Kline", "Okada",
    "Meier", "Dubois", "Ibrahim", "Cohen", "Sato", "Andersen", "Rossi", "Novak",
]
PLACES = {
    SettingFamily.WORKPLACE: ("server room", "lobby", "records office"),
    SettingFamily.DETECTIVE: ("evidence locker", "front desk", "archive"),
    SettingFamily.DOMESTIC: ("study", "kitchen", "garage"),
    SettingFamily.EXPEDITION: ("radio tent", "supply cache", "mess hall"),
    SettingFamily.HISTORICAL: ("scriptorium", "courtyard", "gatehouse"),
    SettingFamily.SPECULATIVE: ("core chamber", "airlock foyer", "data vault"),
}
ACTIONS = {
    SettingFamily.WORKPLACE: (
        "reboot the servers",
        "rebooted the servers",
        "servers_rebooted",
        "master badge",
        "Rebooting the servers",
    ),
    SettingFamily.DETECTIVE: (
        "remove the sealed file",
        "removed the sealed file",
        "artifact_taken",
        "vault key",
        "Removing the sealed file",
    ),
    SettingFamily.DOMESTIC: (
        "disable the furnace lock",
        "disabled the furnace lock",
        "key_action",
        "spare key",
        "Disabling the furnace lock",
    ),
    SettingFamily.EXPEDITION: (
        "transmit the abort code",
        "transmitted the abort code",
        "key_action",
        "command token",
        "Transmitting the abort code",
    ),
    SettingFamily.HISTORICAL: (
        "open the sealed chest",
        "opened the sealed chest",
        "artifact_taken",
        "warden's seal",
        "Opening the sealed chest",
    ),
    SettingFamily.SPECULATIVE: (
        "trip the containment reset",
        "tripped the containment reset",
        "servers_rebooted",
        "override chip",
        "Tripping the containment reset",
    ),
}
ROLES = [
    "shift lead",
    "analyst",
    "technician",
    "coordinator",
    "archivist",
    "liaison",
]


def _rng_names(seed: int, n: int) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    # Force at least one shared surname to block last-name heuristics.
    shared_last = LAST[hashlib.sha256(f"{seed}:last".encode()).digest()[0] % len(LAST)]
    for i in range(n):
        h = hashlib.sha256(f"{seed}:{i}:name".encode()).digest()
        first = FIRST[h[0] % len(FIRST)]
        last = shared_last if i < 2 else LAST[h[1] % len(LAST)]
        eid = f"p{i}"
        label = f"{first} {last}"
        # guarantee unique full labels
        suffix = 2
        while any(x[2] == label for x in out):
            label = f"{first} {last}-{suffix}"
            suffix += 1
        out.append((eid, first, label))
    return out


def _force_shared_answer_firstname(
    names: list[tuple[str, str, str]],
    answer_idx: int,
    seed: int,
) -> list[tuple[str, str, str]]:
    """Ensure another suspect shares the answer's given name (blocks first-name shortcuts)."""
    if len(names) < 2:
        return names
    answer_id, answer_first, answer_label = names[answer_idx]
    other_idx = (answer_idx + 2) % len(names)
    if other_idx == answer_idx:
        other_idx = (answer_idx + 1) % len(names)
    eid, _old_first, _old_label = names[other_idx]
    # Keep a distinct surname from the answer.
    answer_last = answer_label.split()[-1]
    h = hashlib.sha256(f"{seed}:sharefirst".encode()).digest()
    last = LAST[h[0] % len(LAST)]
    if last == answer_last:
        last = LAST[(h[0] + 1) % len(LAST)]
    label = f"{answer_first} {last}"
    suffix = 2
    existing = {x[2] for i, x in enumerate(names) if i != other_idx}
    while label in existing:
        label = f"{answer_first} {last}-{suffix}"
        suffix += 1
    names = list(names)
    names[other_idx] = (eid, answer_first, label)
    return names


@dataclass
class TemplateBundle:
    world: WorldSpec
    visible: VisibleTheory
    story: StoryDocument
    questions: QuestionBundle
    n_hops: int


def build_access_timeline(recipe: GenerationRecipe) -> TemplateBundle:
    """Instantiate access/timeline mystery with unique visible theory."""
    names = _rng_names(recipe.seed, recipe.n_suspects)
    answer_idx = hashlib.sha256(f"{recipe.seed}:ans".encode()).digest()[0] % recipe.n_suspects
    names = _force_shared_answer_firstname(names, answer_idx, recipe.seed)
    lender_idx = (answer_idx + 1) % recipe.n_suspects
    if lender_idx == answer_idx:
        lender_idx = (answer_idx + 2) % recipe.n_suspects

    place_secure, place_public, place_other = PLACES[recipe.setting_family]
    action_phrase, action_past, effect_atom, item_name, action_gerund = ACTIONS[
        recipe.setting_family
    ]
    secure_id, public_id, item_id = "place_secure", "place_public", "item_key"

    entities = [
        Entity(id=eid, type="person", label=label, aliases=[first, label])
        for eid, first, label in names
    ]
    entities.extend(
        [
            Entity(id=secure_id, type="place", label=place_secure.title()),
            Entity(id=public_id, type="place", label=place_public.title()),
            Entity(id=item_id, type="object", label=item_name.title()),
        ]
    )

    answer_id = names[answer_idx][0]
    lender_id = names[lender_idx][0]

    relations: list[Relation] = []
    for eid, _, _ in names:
        if eid in {answer_id, lender_id}:
            relations.append(
                Relation(
                    id=f"rel_access_{eid}",
                    kind=RelationKind.HAS_ACCESS,
                    subject=eid,
                    object=secure_id,
                )
            )
        else:
            relations.append(
                Relation(
                    id=f"rel_access_pub_{eid}",
                    kind=RelationKind.HAS_ACCESS,
                    subject=eid,
                    object=public_id,
                )
            )
    relations.append(
        Relation(
            id="rel_owns",
            kind=RelationKind.OWNS,
            subject=lender_id,
            object=item_id,
        )
    )

    times = [
        TimePoint(id="t1", label="09:00", order=1),
        TimePoint(id="t2", label="09:25", order=2),
        TimePoint(id="t3", label="09:50", order=3),
        TimePoint(id="t4", label="10:10", order=4),
    ]

    events = [
        Event(
            id="e_loan",
            label=f"{names[lender_idx][2]} lends the {item_name}",
            actor=lender_id,
            time_point="t1",
            effects=[f"holds_{answer_id}"],
        ),
        Event(
            id="e_action",
            label=action_phrase,
            actor=answer_id,
            time_point="t3",
            preconditions=[f"holds_{answer_id}", f"has_access_{answer_id}_{secure_id}"],
            effects=[effect_atom],
            causal_parents=["e_loan"],
        ),
        Event(
            id="e_alarm",
            label="Alarm / discovery",
            time_point="t4",
            preconditions=[effect_atom],
            effects=["discovered"],
            causal_parents=["e_action"],
        ),
    ]
    for eid, _, label in names:
        if eid not in {answer_id, lender_id}:
            events.append(
                Event(
                    id=f"e_idle_{eid}",
                    label=f"{label} remains at {place_public}",
                    actor=eid,
                    time_point="t2",
                    effects=[f"idle_{eid}"],
                )
            )

    world = WorldSpec(
        id=f"world-{recipe.seed}",
        entities=entities,
        relations=relations,
        time_points=times,
        events=events,
        rules=[
            Rule(
                id="rule_access",
                text=(
                    f"Only people with access to the {place_secure} can "
                    f"{action_phrase}."
                ),
                formal="requires_access",
            ),
            Rule(
                id="rule_item",
                text=f"The action requires holding the {item_name}.",
                formal="requires_item",
            ),
        ],
        facts=[
            f"has_access_{answer_id}_{secure_id}",
            f"has_access_{lender_id}_{secure_id}",
        ],
        target=TargetClaim(
            predicate="acted_by",
            arguments=["target"],
            expected_value=answer_id,
        ),
        intervention=Intervention(
            id="iv1",
            description=f"If the {item_name} is never lent",
            disable_event="e_loan",
            expected_target_value="none",
        ),
        answer_entity=answer_id,
        candidate_answers=[eid for eid, _, _ in names],
    )

    answer_label = names[answer_idx][2]
    lender_label = names[lender_idx][2]
    answer_first = names[answer_idx][1]
    answer_last = answer_label.split()[-1]
    twin_idx = next(
        i
        for i, (eid, first, _label) in enumerate(names)
        if i != answer_idx and first == answer_first
    )
    twin_id, _twin_first, twin_label = names[twin_idx]
    twin_last = twin_label.split()[-1]

    code_by_id = {
        eid: f"EMP-{(recipe.seed + i * 17) % 89 + 10}"
        for i, (eid, _, _) in enumerate(names)
    }
    answer_code = code_by_id[answer_id]
    lender_code = code_by_id[lender_id]
    twin_code = code_by_id[twin_id]
    locker_ans = f"L-{(recipe.seed % 40) + 10}"
    locker_twin = f"L-{((recipe.seed * 3) % 40) + 10}"
    if locker_twin == locker_ans:
        locker_twin = f"L-{(recipe.seed % 40) + 11}"

    facts: list[VisibleFact] = [
        VisibleFact(
            id="f_rule_access",
            text=(
                f"Posted rule: {action_gerund} is impossible without an authorized "
                f"{place_secure} credential."
            ),
            formal=f"requires_access:{secure_id}",
            channel=ClueChannel.RULE_APPLICATION,
            role="required",
            scene_id="sc1",
            reveal_order=1,
        ),
        VisibleFact(
            id="f_acc_ans",
            text=(
                f"A faded authorization sheet for the {place_secure} includes "
                f"code {answer_code}."
            ),
            formal=f"has_access:{answer_id}:{secure_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=2,
        ),
        VisibleFact(
            id="f_acc_lender",
            text=(
                f"The same sheet also lists code {lender_code} for the "
                f"{place_secure}."
            ),
            formal=f"has_access:{lender_id}:{secure_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=3,
        ),
        VisibleFact(
            id="f_code_map_ans",
            text=(
                f"A torn badge legend fragment pairs {answer_code} with the given name "
                f"{answer_first} only; the surname field is smudged."
            ),
            formal=f"code_map:{answer_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=12,
        ),
        VisibleFact(
            id="f_locker_assign",
            text=(
                f"Facilities roster: locker {locker_ans} is assigned to badge "
                f"{answer_code}."
            ),
            formal=f"locker_assign:{answer_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc2",
            reveal_order=14,
        ),
        VisibleFact(
            id="f_surname_ans",
            text=(
                f"Inside locker {locker_ans}, a mail-stop strip shows the surname "
                f"{answer_last} with no given name printed."
            ),
            formal=f"surname_map:{answer_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc3",
            reveal_order=61,
        ),
        VisibleFact(
            id="f_locker_twin",
            text=(
                f"Facilities roster: locker {locker_twin} is assigned to badge "
                f"{twin_code}."
            ),
            formal=f"locker_assign:{twin_id}",
            channel=ClueChannel.RECORD,
            role="distractor",
            scene_id="sc2",
            reveal_order=15,
        ),
        VisibleFact(
            id="f_surname_twin",
            text=(
                f"Inside locker {locker_twin}, another strip shows the surname "
                f"{twin_last} with no given name printed."
            ),
            formal=f"surname_map:{twin_id}",
            channel=ClueChannel.RECORD,
            role="distractor",
            scene_id="sc1",
            reveal_order=16,
        ),
        VisibleFact(
            id="f_code_map_lender",
            text=f"Personnel index: {lender_code} resolves to {lender_label}.",
            formal=f"code_map:{lender_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=13,
        ),
        VisibleFact(
            id="f_rule_item",
            text=(
                f"An engineering note warns that without the {item_name}, nobody can "
                f"successfully {action_phrase}."
            ),
            formal=f"requires_item:{item_id}",
            channel=ClueChannel.RULE_APPLICATION,
            role="required",
            scene_id="sc2",
            reveal_order=4,
        ),
        VisibleFact(
            id="f_holds",
            text=(
                f"At 09:25 a reflection on a polished panel shows only a badge "
                f"glint reading {answer_code} beside the {item_name}."
            ),
            formal=f"holds:{answer_id}:{item_id}",
            channel=ClueChannel.OBSERVATION,
            role="required",
            scene_id="sc2",
            reveal_order=5,
        ),
        VisibleFact(
            id="f_elim_lender",
            text=(
                f"At 09:00, {lender_code} completed a handoff of the {item_name} "
                f"and immediately took a shuttle toward the {place_other}, "
                f"remaining there through the alarm."
            ),
            formal=f"eliminated:{lender_id}",
            channel=ClueChannel.STATEMENT,
            role="required",
            scene_id="sc2",
            reveal_order=6,
        ),
    ]

    order = 7
    elim_templates = [
        (
            "Sign-in strips place {code} at the {public} from 09:10 to 10:05 "
            "with no door event at the {secure}."
        ),
        (
            "A camera summary shows {code} lingering near the {public} through "
            "the critical window, never approaching the {secure}."
        ),
        (
            "Radio check-ins keep {code} accounted for at the {public} from "
            "09:15 onward; the {secure} log stays blank for that badge."
        ),
        (
            "A handwritten roster marks {code} as covering the {public} desk "
            "until after 10:10, with no {secure} visit recorded."
        ),
    ]
    elim_i = 0
    for eid, _, _label in names:
        if eid in {answer_id, lender_id}:
            continue
        code = code_by_id[eid]
        tmpl = elim_templates[elim_i % len(elim_templates)]
        elim_i += 1
        facts.append(
            VisibleFact(
                id=f"f_elim_{eid}",
                text=tmpl.format(code=code, public=place_public, secure=place_secure),
                formal=f"eliminated:{eid}",
                channel=ClueChannel.OBSERVATION,
                role="required",
                scene_id="sc3",
                reveal_order=order,
            )
        )
        order += 1

    used_distractors: set[str] = set()
    for i in range(recipe.n_distractors):
        line = _distractor_line(recipe.seed, i, recipe.setting_family, place_public)
        # Avoid duplicate distractor sentences in the same story.
        attempt = 0
        while line in used_distractors and attempt < len(_DISTRACTOR_OPTIONS):
            attempt += 1
            line = _distractor_line(
                recipe.seed + attempt * 17, i, recipe.setting_family, place_public
            )
        used_distractors.add(line)
        facts.append(
            VisibleFact(
                id=f"d{i}",
                text=line,
                formal=f"distractor:{i}",
                channel=ClueChannel.RECORD,
                role="distractor",
                scene_id="sc1" if i % 2 == 0 else "sc3",
                reveal_order=100 + i,
            )
        )

    if recipe.difficulty_bucket in {DifficultyBucket.HARD, DifficultyBucket.VERY_HARD}:
        for f in facts:
            if f.id == "f_holds":
                f.reveal_order = 55
                f.scene_id = "sc3"
            if f.id == "f_code_map_ans":
                f.reveal_order = 8
                f.scene_id = "sc1"
            if f.id == "f_locker_assign":
                f.reveal_order = 40
                f.scene_id = "sc2"
            if f.id == "f_surname_ans":
                f.reveal_order = 70
                f.scene_id = "sc3"
            if f.id == "f_surname_twin":
                f.reveal_order = 9
                f.scene_id = "sc1"
            if f.id == "f_locker_twin":
                f.reveal_order = 41
                f.scene_id = "sc2"
            if f.id.startswith("f_elim_") and f.id != "f_elim_lender":
                f.reveal_order += 30

    visible = VisibleTheory(id=f"vis-{recipe.seed}", world_id=world.id, facts=facts)
    story = render_story(
        recipe,
        names,
        answer_id,
        lender_id,
        place_secure,
        place_public,
        place_other,
        item_name,
        action_phrase,
        action_past,
        action_gerund,
        facts,
        code_by_id,
    )
    label_by_id = {eid: label for eid, _, label in names}

    questions = _build_questions(
        action_past=action_past,
        item_name=item_name,
        answer_label=answer_label,
        lender_label=lender_label,
        answer_code=answer_code,
        false_h=next(eid for eid, _, _ in names if eid != answer_id),
        label_by_id=label_by_id,
        answer_id=answer_id,
        lender_id=lender_id,
    )
    n_hops = max(recipe.target_hops, len([f for f in facts if f.role == "required"]))
    return TemplateBundle(
        world=world,
        visible=visible,
        story=story,
        questions=questions,
        n_hops=n_hops,
    )


def _build_questions(
    *,
    action_past: str,
    item_name: str,
    answer_label: str,
    lender_label: str,
    answer_code: str,
    false_h: str,
    label_by_id: dict[str, str],
    answer_id: str,
    lender_id: str,
) -> QuestionBundle:
    answer_variants = name_answer_variants(answer_label)
    lender_variants = name_answer_variants(lender_label)
    scored = [
        ScoredQuestion(
            id="q_main",
            question=(
                f"Provide the full name (given name and surname) of the person who "
                f"{action_past}."
            ),
            gold_answer=answer_label,
            gold_answer_variants=answer_variants,
            question_type="main",
        ),
        ScoredQuestion(
            id="q_lender",
            question=(
                f"Provide the full name (given name and surname) of the person who "
                f"handed over the {item_name} at 09:00."
            ),
            gold_answer=lender_label,
            gold_answer_variants=lender_variants,
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If the {item_name} had never been lent, who would have "
                f"{action_past}? Answer with the full name (given name and surname), "
                f"or exactly 'none' if nobody could have done it."
            ),
            gold_answer="none",
            gold_answer_variants=["none", "Nobody", "no one"],
            question_type="counterfactual",
        ),
        ScoredQuestion(
            id="q_code",
            question=(
                f"Which badge code was seen beside the {item_name} at 09:25? "
                f"Answer with the exact code only (for example EMP-12)."
            ),
            gold_answer=answer_code,
            gold_answer_variants=[answer_code, answer_code.upper(), answer_code.lower()],
            question_type="code",
        ),
    ]
    cf_q = scored[2].question
    return QuestionBundle(
        main_question=scored[0].question,
        gold_answer=answer_label,
        questions=scored,
        supported_conclusions=[
            f"Only {answer_label} and {lender_label} had secure-area access.",
            f"{answer_label} held the {item_name} after 09:00.",
            f"{lender_label} no longer held the {item_name} at action time.",
        ],
        counterfactual=CounterfactualTask(
            question=cf_q,
            answer="none",
            intervention=f"disable e_loan ({item_name} never lent)",
        ),
        falsifier=FalsifierTask(
            hypothesis=f"{label_by_id[false_h]} did it",
            minimal_evidence=(
                [f"f_elim_{false_h}"]
                if false_h not in {answer_id, lender_id}
                else ["f_elim_lender", "f_holds"]
            ),
        ),
    )


_DISTRACTOR_OPTIONS = [
    "A maintenance ticket about the {public} lights was filed at 08:40.",
    "Someone complained that the coffee machine jammed before opening.",
    "A delivery driver signed in and left a package at reception.",
    "The night guard reported an uneventful patrol at 07:15.",
    "An unrelated badge was reported missing last week and later found.",
    "A calendar invite for a budget review sat untouched on a shared screen.",
]


def _distractor_line(seed: int, i: int, setting: SettingFamily, public: str) -> str:
    h = hashlib.sha256(f"{seed}:d:{i}:{setting.value}".encode()).digest()[0]
    return _DISTRACTOR_OPTIONS[h % len(_DISTRACTOR_OPTIONS)].format(public=public)


def render_story(
    recipe: GenerationRecipe,
    names: list[tuple[str, str, str]],
    answer_id: str,
    lender_id: str,
    place_secure: str,
    place_public: str,
    place_other: str,
    item_name: str,
    action_phrase: str,
    action_past: str,
    action_gerund: str,
    facts: list[VisibleFact],
    code_by_id: dict[str, str],
) -> StoryDocument:
    """Assemble a coherent multi-paragraph sentence-addressable mystery."""
    by_id = {f.id: f for f in facts}
    role_by_eid = {
        eid: ROLES[
            hashlib.sha256(f"{recipe.seed}:{eid}:role".encode()).digest()[0] % len(ROLES)
        ]
        for eid, _, _ in names
    }

    opening = {
        SettingFamily.WORKPLACE: (
            "The operations floor was already tense when the morning shift began. "
            f"By midmorning it was clear that someone had {action_past}, and the "
            f"{place_secure} bore the marks of an authorized entry."
        ),
        SettingFamily.DETECTIVE: (
            "The precinct's morning briefing broke apart when the alarm sounded. "
            f"Someone had {action_past}, and the {place_secure} showed a clean but "
            "unauthorized use of credentialed access."
        ),
        SettingFamily.DOMESTIC: (
            "The household woke to an odd silence where a machine should have hummed. "
            f"Before long it was obvious that someone had {action_past}."
        ),
        SettingFamily.EXPEDITION: (
            "Frost still clung to the tent ropes when the first anomaly was logged. "
            f"The team soon confirmed that someone had {action_past}."
        ),
        SettingFamily.HISTORICAL: (
            "Bells had barely finished when the steward called for an accounting. "
            f"Word spread that someone had {action_past}."
        ),
        SettingFamily.SPECULATIVE: (
            "Habitat lighting shifted to amber as the monitoring lattice stuttered. "
            f"Diagnostics showed that someone had {action_past}."
        ),
    }[recipe.setting_family]

    cast_bits = []
    firsts = []
    for eid, first, label in names:
        cast_bits.append(f"{first} ({role_by_eid[eid]})")
        firsts.append(first)
    if len(cast_bits) == 1:
        cast_line = cast_bits[0]
    elif len(cast_bits) == 2:
        cast_line = f"{cast_bits[0]} and {cast_bits[1]}"
    else:
        cast_line = ", ".join(cast_bits[:-1]) + f", and {cast_bits[-1]}"
    cast_para = (
        f"Duty board first names for the shift were {cast_line}. "
        "Surnames were not printed on that board. Colleagues leaned on badge codes "
        "in radio traffic, and at least two people shared a given name, so incomplete "
        "badge legends were easy to misread."
    )

    # Scene 1 — rules and access records (narrative, not a dump)
    sc1_lines = [
        f"Near the {place_secure}, investigators found the standing controls still posted.",
        by_id["f_rule_access"].text,
        by_id["f_acc_ans"].text,
        by_id["f_acc_lender"].text,
        (
            "No other codes appeared on that sheet. Everyone else on duty was limited "
            f"to the {place_public}."
        ),
    ]
    sc1_lines.append(by_id["f_code_map_lender"].text)
    sc1_lines.append(by_id["f_code_map_ans"].text)
    sc1_lines.append(by_id["f_surname_twin"].text)
    distractors = [f for f in facts if f.role == "distractor" and f.id.startswith("d")]
    if distractors:
        sc1_lines.append(
            f"Elsewhere, ordinary noise continued: {distractors[0].text.rstrip('.')}."
        )
    sc1 = " ".join(sc1_lines)

    # Scene 2 — transfer + locker assignments (split from surnames)
    sc2_lines = [
        by_id["f_rule_item"].text,
        by_id["f_elim_lender"].text,
        by_id["f_locker_assign"].text,
        by_id["f_locker_twin"].text,
        (
            f"Witnesses later disagreed about motives. They only agreed the "
            f"{item_name} changed hands once before the critical window, and "
            f"that the recipient was not the original signatory."
        ),
    ]
    sc2 = " ".join(sc2_lines)

    # Scene 3 — movements, holds, answer surname, discovery
    elim_facts = [
        f
        for f in sorted(facts, key=lambda x: x.reveal_order)
        if f.id.startswith("f_elim_") and f.id != "f_elim_lender"
    ]
    sc3_lines: list[str] = []
    if elim_facts:
        sc3_lines.append(
            "Attendance logs for the rest of the morning were blunt and consistent."
        )
        for f in elim_facts:
            sc3_lines.append(f.text)
    sc3_lines.append(by_id["f_holds"].text)
    for d in distractors[1:3]:
        sc3_lines.append(d.text)
    sc3_lines.append(by_id["f_surname_ans"].text)
    sc3_lines.append(
        f"Shortly after 10:10 it became clear that someone {action_past}. "
        f"The {place_secure} showed signs of entry, while idle conversation "
        f"continued near the {place_public}."
    )
    sc3_lines.append(
        _padding_sentence(recipe.seed, 0, place_other, recipe.setting_family)
    )
    sc3 = " ".join(sc3_lines)

    scenes = [
        SceneDraft(
            id="sc1",
            title="Access and early records",
            obligated_fact_ids=[
                f.id for f in facts if f.scene_id == "sc1" and f.role == "required"
            ],
            prose=sc1,
        ),
        SceneDraft(
            id="sc2",
            title="The transfer",
            obligated_fact_ids=[
                f.id for f in facts if f.scene_id == "sc2" and f.role == "required"
            ],
            prose=sc2,
        ),
        SceneDraft(
            id="sc3",
            title="Movements and discovery",
            obligated_fact_ids=[
                f.id for f in facts if f.scene_id == "sc3" and f.role == "required"
            ],
            prose=sc3,
        ),
    ]

    paragraphs = [opening, cast_para, sc1, sc2, sc3]
    full = "\n\n".join(paragraphs)
    sentences = _split_sentences(full)
    for fact in facts:
        for sent in sentences:
            if fact.text[:40] in sent.text:
                fact.sentence_ids.append(sent.id)
                break

    # Sanity: story must mention answer/lender codes (reasoning load-bearing).
    answer_code = code_by_id[answer_id]
    lender_code = code_by_id[lender_id]
    if answer_code not in full or lender_code not in full:
        raise ValueError("story missing load-bearing badge codes")
    # Do not leak the contiguous full-name gold string into the prose.
    answer_label = next(label for eid, _, label in names if eid == answer_id)
    if _story_contains_full_name(full, answer_label):
        raise ValueError("story leaks contiguous gold full name")

    return StoryDocument(
        id=f"story-{recipe.seed}",
        title=f"Incident {recipe.seed}",
        scenes=scenes,
        sentences=sentences,
        full_text=full,
    )


def _story_contains_full_name(text: str, full_name: str) -> bool:
    """True when the exact full name appears as its own token sequence (not a hyphen suffix)."""
    pattern = rf"(?<![\w-]){re.escape(full_name)}(?!-\d)(?![\w-])"
    return re.search(pattern, text) is not None


def _padding_sentence(seed: int, i: int, place_other: str, setting: SettingFamily) -> str:
    lines = [
        (
            f"A clerk mentioned an irrelevant errand near the {place_other} "
            "and then changed the subject."
        ),
        "Radio chatter mixed shift handovers with weather complaints and supply counts.",
        "Nobody treated the early rumors as decisive; they only added texture to the timeline.",
        "A printed checklist floated on a table, half completed and smudged.",
        "Two people argued briefly about lunch schedules before returning to their posts.",
    ]
    h = hashlib.sha256(f"{seed}:pad:{i}:{setting.value}".encode()).digest()[0]
    return lines[h % len(lines)]


def _split_sentences(text: str) -> list[Sentence]:
    raw: list[str] = []
    for para in text.split("\n\n"):
        buf = []
        for ch in para:
            buf.append(ch)
            if ch in ".!?" and (len(buf) > 1):
                raw.append("".join(buf).strip())
                buf = []
        if buf and "".join(buf).strip():
            raw.append("".join(buf).strip())
    return [Sentence(id=f"sent-{i+1}", text=s) for i, s in enumerate(raw) if s]
