"""Template-backed world and story generation for the pilot."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cogito_mill.domain.evidence import ClueChannel, VisibleFact, VisibleTheory
from cogito_mill.domain.narrative import SceneDraft, Sentence, StoryDocument
from cogito_mill.domain.questions import (
    CounterfactualTask,
    FalsifierTask,
    QuestionBundle,
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
    ),
    SettingFamily.DETECTIVE: (
        "remove the sealed file",
        "removed the sealed file",
        "artifact_taken",
        "vault key",
    ),
    SettingFamily.DOMESTIC: (
        "disable the furnace lock",
        "disabled the furnace lock",
        "key_action",
        "spare key",
    ),
    SettingFamily.EXPEDITION: (
        "transmit the abort code",
        "transmitted the abort code",
        "key_action",
        "command token",
    ),
    SettingFamily.HISTORICAL: (
        "open the sealed chest",
        "opened the sealed chest",
        "artifact_taken",
        "warden's seal",
    ),
    SettingFamily.SPECULATIVE: (
        "trip the containment reset",
        "tripped the containment reset",
        "servers_rebooted",
        "override chip",
    ),
}


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


@dataclass
class TemplateBundle:
    world: WorldSpec
    visible: VisibleTheory
    story: StoryDocument
    questions: QuestionBundle
    n_hops: int



def _decoy_personnel(seed: int, n: int = 24) -> list[str]:
    lines: list[str] = []
    for i in range(n):
        h = hashlib.sha256(f"{seed}:decoy:{i}".encode()).digest()
        first = FIRST[h[0] % len(FIRST)]
        last = LAST[h[1] % len(LAST)]
        code = f"EMP-{(seed + 3 * i) % 97 + 10}"
        lines.append(f"Personnel index: {code} resolves to {first} {last}.")
    return lines

def build_access_timeline(recipe: GenerationRecipe) -> TemplateBundle:
    """Instantiate access/timeline mystery with unique visible theory."""
    names = _rng_names(recipe.seed, recipe.n_suspects)
    answer_idx = hashlib.sha256(f"{recipe.seed}:ans".encode()).digest()[0] % recipe.n_suspects
    # prefer not index 0 always
    lender_idx = (answer_idx + 1) % recipe.n_suspects
    if lender_idx == answer_idx:
        lender_idx = (answer_idx + 2) % recipe.n_suspects

    place_secure, place_public, place_other = PLACES[recipe.setting_family]
    action_phrase, action_past, effect_atom, item_name = ACTIONS[recipe.setting_family]
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
    # exactly two people have secure access: answer + lender
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
    # idle presence events for others
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
                text=f"Only people with access to the {place_secure} can {action_phrase}.",
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

    # Indirect codes force multi-hop linking in prose while formal atoms stay unique.
    code_by_id = {
        eid: f"EMP-{(recipe.seed + i * 17) % 89 + 10}"
        for i, (eid, _, _) in enumerate(names)
    }
    answer_code = code_by_id[answer_id]
    lender_code = code_by_id[lender_id]

    facts: list[VisibleFact] = [
        VisibleFact(
            id="f_rule_access",
            text=(
                f"Posted rule: {action_phrase} is impossible without an authorized "
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
                f"{names[answer_idx][1]} only; the surname field is smudged."
            ),
            formal=f"code_map:{answer_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=12,
        ),
        VisibleFact(
            id="f_code_map_lender",
            text=(
                f"Personnel index: {lender_code} resolves to {lender_label}."
            ),
            formal=f"code_map:{lender_id}",
            channel=ClueChannel.RECORD,
            role="required",
            scene_id="sc1",
            reveal_order=13,
        ),
        VisibleFact(
            id="f_rule_item",
            text=(
                f"Engineering note: without the {item_name}, nobody can "
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
    for eid, _, _label in names:
        if eid in {answer_id, lender_id}:
            continue
        code = code_by_id[eid]
        facts.append(
            VisibleFact(
                id=f"f_elim_{eid}",
                text=(
                    f"Sign-in strips place {code} at the {place_public} from 09:10 "
                    f"to 10:05 with no door event at the {place_secure}."
                ),
                formal=f"eliminated:{eid}",
                channel=ClueChannel.OBSERVATION,
                role="required",
                scene_id="sc3",
                reveal_order=order,
            )
        )
        # decoy code maps for non-answers (increase search)
        # Intentionally omit direct code->full-name maps for non-answers.
        order += 1

    # distractors
    for i in range(recipe.n_distractors):
        facts.append(
            VisibleFact(
                id=f"d{i}",
                text=_distractor_line(recipe.seed, i, recipe.setting_family, place_public),
                formal=f"distractor:{i}",
                channel=ClueChannel.RECORD,
                role="distractor",
                scene_id="sc1" if i % 2 == 0 else "sc3",
                reveal_order=100 + i,
            )
        )

    # Hard mode: bury key linking clues and interleave distractors by reveal_order shuffle
    if recipe.difficulty_bucket in {DifficultyBucket.HARD, DifficultyBucket.VERY_HARD}:
        for f in facts:
            if f.id == "f_holds":
                f.reveal_order = 55
                f.scene_id = "sc3"
            if f.id == "f_code_map_ans":
                f.reveal_order = 60
                f.scene_id = "sc3"
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
        facts,
    )
    label_by_id = {eid: label for eid, _, label in names}

    question = f"Who {action_past}?"
    cf_q = (
        f"If {lender_label} never lent the {item_name}, who would have "
        f"{action_past}?"
    )
    false_h = next(eid for eid, _, _ in names if eid != answer_id)

    questions = QuestionBundle(
        main_question=question,
        gold_answer=answer_label,
        supported_conclusions=[
            f"Only {answer_label} and {lender_label} had {place_secure} access.",
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
    # hops from required facts roughly
    n_hops = max(recipe.target_hops, len([f for f in facts if f.role == "required"]))
    return TemplateBundle(
        world=world,
        visible=visible,
        story=story,
        questions=questions,
        n_hops=n_hops,
    )


def _distractor_line(seed: int, i: int, setting: SettingFamily, public: str) -> str:
    options = [
        f"A maintenance ticket about the {public} lights was filed at 08:40.",
        "Someone complained that the coffee machine jammed before opening.",
        "A delivery driver signed in and left a package at reception.",
        "The night guard reported an uneventful patrol at 07:15.",
        "An unrelated badge was reported missing last week and later found.",
        "A calendar invite for a budget review sat untouched on a shared screen.",
    ]
    h = hashlib.sha256(f"{seed}:d:{i}:{setting.value}".encode()).digest()[0]
    return options[h % len(options)]


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
    facts: list[VisibleFact],
) -> StoryDocument:
    """Assemble a multi-paragraph sentence-addressable story."""
    by_scene: dict[str, list[VisibleFact]] = {"sc1": [], "sc2": [], "sc3": []}
    for f in sorted(facts, key=lambda x: x.reveal_order):
        by_scene.setdefault(f.scene_id, []).append(f)

    paragraphs: list[str] = []
    setting_open = {
        SettingFamily.WORKPLACE: (
            "The operations floor was already tense when the morning shift began."
        ),
        SettingFamily.DETECTIVE: (
            "The precinct's morning briefing was interrupted by an urgent alarm."
        ),
        SettingFamily.DOMESTIC: (
            "The household woke to an odd silence where a machine should have hummed."
        ),
        SettingFamily.EXPEDITION: (
            "Frost still clung to the tent ropes when the first anomaly was logged."
        ),
        SettingFamily.HISTORICAL: (
            "Bells had barely finished when the steward called for an accounting."
        ),
        SettingFamily.SPECULATIVE: (
            "Habitat lighting shifted to amber as the monitoring lattice stuttered."
        ),
    }[recipe.setting_family]
    paragraphs.append(setting_open)
    decoys = _decoy_personnel(recipe.seed, n=48)
    # Keep answer/lender true maps out of this noisy block.
    paragraphs.append(" ".join(decoys))

    cast = ", ".join(first for _, first, _ in names[:-1]) + f", and {names[-1][1]}"
    paragraphs.append(
        f"Given names circulating in the first hour included {cast}. Surnames were "
        f"disputed, and badge codes were cited more often than legal names."
    )

    scenes: list[SceneDraft] = []
    titles = {
        "sc1": "Access and early records",
        "sc2": "The transfer",
        "sc3": "Movements and discovery",
    }
    for scene_id in ["sc1", "sc2", "sc3"]:
        lines = [f.text for f in by_scene.get(scene_id, [])]
        prose = " ".join(lines)
        if scene_id == "sc3":
            prose += (
                f" Shortly after 10:10 it became clear that someone "
                f"{action_past}. The {place_secure} showed signs of entry, while "
                f"idle conversation continued near the {place_public}."
            )
        if scene_id == "sc2":
            prose += (
                f" Witnesses later disagreed about motives. They only agreed the "
                f"{item_name} changed hands once before the critical window, and "
                f"that the recipient was not the original signatory."
            )
        scenes.append(
            SceneDraft(
                id=scene_id,
                title=titles[scene_id],
                obligated_fact_ids=[f.id for f in by_scene.get(scene_id, [])],
                prose=prose,
            )
        )
        paragraphs.append(prose)

    # pad for length / difficulty with neutral connective tissue (not new formal facts)
    for i in range(2 + recipe.n_distractors // 2):
        paragraphs.append(
            _padding_sentence(recipe.seed, i, place_other, recipe.setting_family)
        )

    full = "\n\n".join(paragraphs)
    sentences = _split_sentences(full)
    # map facts to sentence ids by substring match
    for fact in facts:
        for sent in sentences:
            if fact.text[:40] in sent.text:
                fact.sentence_ids.append(sent.id)
                break
    return StoryDocument(
        id=f"story-{recipe.seed}",
        title=f"Incident {recipe.seed}",
        scenes=scenes,
        sentences=sentences,
        full_text=full,
    )


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
