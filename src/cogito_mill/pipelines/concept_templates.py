"""Diverse, solver-checked concept-induction puzzle portfolio."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from cogito_mill.domain.appendix import (
    ChecksumCheckpoint,
    ChecksumParams,
    EvidenceIntervention,
    SolverAppendix,
    StatusCell,
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
    setting_family: SettingFamily
    incident: str
    branch_nouns: tuple[str, ...]


FAMILIES = (
    FamilySpec(
        "watch_handover",
        "concordant watchkeeper",
        "an icebound research vessel changing watches during a storm",
        SettingFamily.EXPEDITION,
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
        SettingFamily.HISTORICAL,
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
        SettingFamily.SPECULATIVE,
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
        SettingFamily.WORKPLACE,
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
        SettingFamily.EXPEDITION,
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
        SettingFamily.WORKPLACE,
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
    appendix: SolverAppendix
    setting_family: SettingFamily


def family_for_seed(seed: int) -> FamilySpec:
    return FAMILIES[(seed // len(FAMILIES)) % len(FAMILIES)]


def build_concept_puzzle(recipe: GenerationRecipe) -> ConceptPuzzle:
    """Build one portfolio member with a unique Horn-theory answer."""
    family = family_for_seed(recipe.seed)
    names = _names(recipe.seed, recipe.n_suspects)
    answer_idx = _pick(recipe.seed, "answer", len(names))
    runner_idx = (answer_idx + 1 + _pick(recipe.seed, "runner", len(names) - 1)) % len(names)
    if runner_idx == answer_idx:
        runner_idx = (runner_idx + 1) % len(names)
    answer_id, answer_label = names[answer_idx]
    runner_id, runner_label = names[runner_idx]
    labels = {person_id: label for person_id, label in names}

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
    status_matrix: dict[str, dict[str, StatusCell]] = {label: {} for _pid, label in names}
    for branch_idx, branch in enumerate(BRANCHES):
        noun = family.branch_nouns[branch_idx]
        for person_id, _label in names:
            status_by_person[person_id][branch] = assignments[branch][person_id]

        for person_idx, (person_id, label) in enumerate(names):
            status = assignments[branch][person_id]
            fact_id = f"f_{branch}_{person_id}"
            atom = LogicAtom(
                predicate="derived_status",
                arguments=[branch, person_id, status],
            )
            logic_facts.append(atom)
            visible_facts.append(
                _visible(
                    fact_id,
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
            status_matrix[label][branch] = StatusCell(
                status=status,
                fact_id=fact_id,
                stream=branch,
                noun=noun,
            )
            order += 1

    weights, coefficients, start_value, modulus, cycle_count, checksums = _checksum_plan(
        recipe.seed,
        status_by_person,
        answer_id=answer_id,
        runner_id=runner_id,
    )
    weight_bits = [
        f"{status} counted as {weight}"
        for status, weight in sorted(weights.items(), key=lambda item: item[1])
    ]
    for status, weight in weights.items():
        logic_facts.append(
            LogicAtom(predicate="status_weight", arguments=[status, str(weight)])
        )
    weight_fact = VisibleFact(
        id="f_status_weights",
        text=(
            "The panel fixed one shared status scale for the whole inquiry: "
            + "; ".join(weight_bits)
            + "."
        ),
        formal="rule:status_weights",
        channel=ClueChannel.RULE_APPLICATION,
        role="required",
        scene_id="sc1",
        reveal_order=order,
    )
    visible_facts.append(weight_fact)
    order += 1

    formula_fact = VisibleFact(
        id="f_checksum_formula",
        text=(
            f"The local tally began at {start_value}. In order it used relation, temporal, "
            "causal, spatial, sequence, and protocol statuses with coefficients "
            f"{', '.join(str(c) for c in coefficients)}. At each stream, the panel squared "
            "the current tally, added that stream's coefficient times its status value, "
            f"and kept the remainder modulo {modulus}. It made three passes: first in the "
            "stated order, then in reverse order with the coefficients reversed, then once "
            "more in the stated order with the coefficient list rotated one place left. "
            "Without resetting the tally, it repeated that complete three-pass cycle "
            f"{cycle_count} times."
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
            explanation=(f"Apply the disclosed iterated modulo-{modulus} tally to {person_id}."),
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
            (f"For this incident, the accepted tally was {checksums[answer_id]}."),
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
            f"The title {family.concept} belongs to the person whose tally matches the key."
        ),
    )
    rules.append(final_rule)
    visible_facts.append(
        _rule_visible(
            final_rule,
            (
                f"The final definition was strict: the {family.concept} was the one person "
                "whose six-stream tally equaled the accepted tally."
            ),
            "sc5",
            order,
        )
    )

    intervention = _find_evidence_intervention(
        family=family,
        names=names,
        status_by_person=status_by_person,
        weights=weights,
        coefficients=coefficients,
        start_value=start_value,
        modulus=modulus,
        cycle_count=cycle_count,
        answer_id=answer_id,
        accepted_key=checksums[answer_id],
    )

    visible = VisibleTheory(
        id=f"vis-{recipe.seed}",
        world_id=f"world-{recipe.seed}",
        facts=visible_facts,
        logic=LogicTheory(facts=logic_facts, rules=rules),
    )
    world = _world(recipe, names, answer_id, family, intervention)
    questions = _questions(
        recipe,
        family,
        answer_label,
        runner_label,
        str(checksums[answer_id]),
        intervention,
        status_by_person,
        labels,
    )
    draft = _offline_draft(recipe, family, visible_facts)
    answer_fact_ids = [f"f_{branch}_{answer_id}" for branch in BRANCHES]
    falsifier = FalsifierTask(
        hypothesis=f"{intervention.person_label} already qualifies under the original record",
        minimal_evidence=[
            "f_checksum_key",
            "f_checksum_formula",
            *answer_fact_ids,
            *intervention.fact_ids(),
        ],
    )
    questions = questions.model_copy(update={"falsifier": falsifier})
    appendix = _build_appendix(
        recipe=recipe,
        family=family,
        names=names,
        status_matrix=status_matrix,
        weights=weights,
        coefficients=coefficients,
        start_value=start_value,
        modulus=modulus,
        cycle_count=cycle_count,
        checksums=checksums,
        status_by_person=status_by_person,
        intervention=intervention,
        falsifier=falsifier,
        supported_conclusions=questions.supported_conclusions,
    )
    # Structural multi-hop count: one hop per person-stream status plus
    # shared scale, procedure, key match. Cycle depth remains in the formula
    # for computational hardness but is not inflated into n_hops.
    n_hops = recipe.n_suspects * len(BRANCHES) + 3
    return ConceptPuzzle(
        family_id=family.id,
        world=world,
        visible=visible,
        questions=questions,
        offline_draft=draft,
        n_hops=n_hops,
        appendix=appendix,
        setting_family=family.setting_family,
    )


def _names(seed: int, n: int) -> list[tuple[str, str]]:
    """Pick unique full names without numeric suffixes."""
    pairs = [(first, last) for first in FIRST for last in LAST]
    ordered = sorted(
        pairs,
        key=lambda pair: hashlib.sha256(
            f"{seed}:concept-name:{pair[0]}:{pair[1]}".encode()
        ).digest(),
    )
    if n > len(ordered):
        raise ValueError(f"need {n} unique names but only {len(ordered)} available")
    return [(f"p{i}", f"{first} {last}") for i, (first, last) in enumerate(ordered[:n])]


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
) -> tuple[dict[str, int], tuple[int, ...], int, int, int, dict[str, int]]:
    status_order = _permutation(seed, "checksum-weights", STATUS_BANK)
    weights = {status: index for index, status in enumerate(status_order)}
    base_coefficients = (2, 3, 5, 7, 11, 13)
    start_value = 2 + seed % 17
    # Keep high cycle depth for unaided hardness; appendix checkpoints make it auditable.
    cycle_count = 97 + seed % 31
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
                    cycle_count=cycle_count,
                )
            checksum_values = list(checksums.values())
            if (
                checksum_values.count(checksums[answer_id]) == 1
                and checksum_values.count(checksums[runner_id]) == 1
                and checksums[answer_id] != checksums[runner_id]
            ):
                return (
                    weights,
                    coefficients,
                    start_value,
                    modulus,
                    cycle_count,
                    checksums,
                )
    raise ValueError("could not construct unique checksum targets")


def iterated_checksum(
    values: tuple[int, ...],
    coefficients: tuple[int, ...],
    *,
    start_value: int,
    modulus: int,
    cycle_count: int,
) -> int:
    """Execute the disclosed forward/reverse/rotated nonlinear recurrence."""
    return checksum_after_cycles(
        values,
        coefficients,
        start_value=start_value,
        modulus=modulus,
        cycle_count=cycle_count,
    )


def checksum_after_cycles(
    values: tuple[int, ...],
    coefficients: tuple[int, ...],
    *,
    start_value: int,
    modulus: int,
    cycle_count: int,
) -> int:
    checksum = start_value
    passes = (
        (values, coefficients),
        (tuple(reversed(values)), tuple(reversed(coefficients))),
        (values, coefficients[1:] + coefficients[:1]),
    )
    for _cycle in range(cycle_count):
        for pass_values, pass_coefficients in passes:
            for value, coefficient in zip(
                pass_values,
                pass_coefficients,
                strict=True,
            ):
                checksum = (checksum * checksum + coefficient * value) % modulus
    return checksum


def _find_evidence_intervention(
    *,
    family: FamilySpec,
    names: list[tuple[str, str]],
    status_by_person: dict[str, dict[str, str]],
    weights: dict[str, int],
    coefficients: tuple[int, ...],
    start_value: int,
    modulus: int,
    cycle_count: int,
    answer_id: str,
    accepted_key: int,
) -> EvidenceIntervention:
    """Find a minimal evidence edit that changes the unique qualifier.

    With a fixed accepted tally, a single non-answer status flip cannot produce a
    different unique qualifier (it either leaves the answer unique or creates a tie).
    Prefer a two-fact edit that moves the title to another person; fall back to a
    one-fact edit on the answer person that yields ``none``.
    """
    labels = {person_id: label for person_id, label in names}

    def _checksum_for(statuses: dict[str, str]) -> int:
        values = tuple(weights[statuses[b]] for b in BRANCHES)
        return iterated_checksum(
            values,
            coefficients,
            start_value=start_value,
            modulus=modulus,
            cycle_count=cycle_count,
        )

    # Precompute single-branch flips that knock the answer off the key.
    answer_off: list[tuple[int, str, str]] = []
    for branch_idx, branch in enumerate(BRANCHES):
        original = status_by_person[answer_id][branch]
        for alt in STATUS_BANK:
            if alt == original:
                continue
            trial_status = dict(status_by_person[answer_id])
            trial_status[branch] = alt
            if _checksum_for(trial_status) != accepted_key:
                answer_off.append((branch_idx, original, alt))

    # Precompute single-branch flips that put each other person onto the key.
    for other_id, _label in names:
        if other_id == answer_id:
            continue
        for branch_idx, branch in enumerate(BRANCHES):
            original = status_by_person[other_id][branch]
            for alt in STATUS_BANK:
                if alt == original:
                    continue
                trial_status = dict(status_by_person[other_id])
                trial_status[branch] = alt
                if _checksum_for(trial_status) != accepted_key:
                    continue
                if not answer_off:
                    continue
                answer_branch_idx, answer_original, answer_alt = answer_off[0]
                other_branch = BRANCHES[branch_idx]
                answer_branch = BRANCHES[answer_branch_idx]
                return EvidenceIntervention(
                    person_id=other_id,
                    person_label=labels[other_id],
                    branch=other_branch,
                    noun=family.branch_nouns[branch_idx],
                    fact_id=f"f_{other_branch}_{other_id}",
                    from_status=original,
                    to_status=alt,
                    answer_label=labels[other_id],
                    secondary_person_id=answer_id,
                    secondary_person_label=labels[answer_id],
                    secondary_branch=answer_branch,
                    secondary_noun=family.branch_nouns[answer_branch_idx],
                    secondary_fact_id=f"f_{answer_branch}_{answer_id}",
                    secondary_from_status=answer_original,
                    secondary_to_status=answer_alt,
                )

    # Fallback: one edit on the answer person yields no qualifier.
    if answer_off:
        branch_idx, original, alt = answer_off[0]
        branch = BRANCHES[branch_idx]
        return EvidenceIntervention(
            person_id=answer_id,
            person_label=labels[answer_id],
            branch=branch,
            noun=family.branch_nouns[branch_idx],
            fact_id=f"f_{branch}_{answer_id}",
            from_status=original,
            to_status=alt,
            answer_label="none",
        )
    raise ValueError("could not construct minimal evidence-edit counterfactual")


def _world(
    recipe: GenerationRecipe,
    names: list[tuple[str, str]],
    answer_id: str,
    family: FamilySpec,
    intervention: EvidenceIntervention,
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
            id="iv_evidence_status",
            description=intervention.question_clause(),
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
    intervention: EvidenceIntervention,
    status_by_person: dict[str, dict[str, str]],
    labels: dict[str, str],
) -> QuestionBundle:
    main = MAIN_STEMS[recipe.seed % len(MAIN_STEMS)].format(concept=family.concept)
    probe_branch = BRANCHES[_pick(recipe.seed, "probe-branch", len(BRANCHES))]
    probe_noun = family.branch_nouns[BRANCHES.index(probe_branch)]
    probe_person_id = next(pid for pid, label in labels.items() if label == runner)
    probe_status = status_by_person[probe_person_id][probe_branch]
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
                f"According to the surviving record, what status was assigned to "
                f"{runner}'s {probe_noun}? Answer with the exact status word."
            ),
            gold_answer=probe_status,
            gold_answer_variants=[probe_status],
            question_type="intermediate",
        ),
        ScoredQuestion(
            id="q_counterfactual",
            question=(
                f"If {intervention.question_clause()}, while every other record stayed fixed, "
                f"who would become the {family.concept}? "
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
            id="q_protocol_key",
            question="What exact integer tally did the board accept?",
            gold_answer=checksum_key,
            gold_answer_variants=[checksum_key],
            question_type="scalar",
        ),
    ]
    return QuestionBundle(
        main_question=main,
        gold_answer=answer,
        questions=questions,
        supported_conclusions=[
            f"{answer}'s six-stream tally equals the accepted tally.",
            (
                f"After the evidence edit ({intervention.question_clause()}), "
                f"the unique result is {intervention.answer_label}."
            ),
        ],
        counterfactual=CounterfactualTask(
            question=questions[2].question,
            answer=intervention.answer_label,
            intervention=intervention.question_clause(),
        ),
        falsifier=FalsifierTask(
            hypothesis=(
                f"{intervention.person_label} already qualifies under the original record"
            ),
            minimal_evidence=["f_checksum_key", *intervention.fact_ids()],
        ),
    )


def _build_appendix(
    *,
    recipe: GenerationRecipe,
    family: FamilySpec,
    names: list[tuple[str, str]],
    status_matrix: dict[str, dict[str, StatusCell]],
    weights: dict[str, int],
    coefficients: tuple[int, ...],
    start_value: int,
    modulus: int,
    cycle_count: int,
    checksums: dict[str, int],
    status_by_person: dict[str, dict[str, str]],
    intervention: EvidenceIntervention,
    falsifier: FalsifierTask,
    supported_conclusions: list[str],
) -> SolverAppendix:
    labels = {person_id: label for person_id, label in names}
    candidate_checksums = {labels[pid]: value for pid, value in checksums.items()}
    checkpoints: list[ChecksumCheckpoint] = []
    checkpoint_cycles = sorted(
        {
            0,
            max(1, cycle_count // 3),
            max(2, (2 * cycle_count) // 3),
            cycle_count,
        }
    )
    focus_ids = [pid for pid, _ in names[:2]]
    for person_id in focus_ids:
        values = tuple(weights[status_by_person[person_id][branch]] for branch in BRANCHES)
        for after in checkpoint_cycles:
            checkpoints.append(
                ChecksumCheckpoint(
                    after_cycles=after,
                    person_id=person_id,
                    person_label=labels[person_id],
                    value=checksum_after_cycles(
                        values,
                        coefficients,
                        start_value=start_value,
                        modulus=modulus,
                        cycle_count=after,
                    ),
                )
            )
    return SolverAppendix(
        id=f"lss-concept-{recipe.seed:06d}",
        status_matrix=status_matrix,
        weights=weights,
        checksum_params=ChecksumParams(
            start_value=start_value,
            coefficients=list(coefficients),
            modulus=modulus,
            cycle_count=cycle_count,
            branch_order=list(BRANCHES),
        ),
        candidate_checksums=candidate_checksums,
        checkpoints=checkpoints,
        supported_conclusions=supported_conclusions,
        evidence_counterfactual=intervention,
        falsifier=falsifier,
        notes=[
            "Thin Hub items stay story-only; this appendix is a companion audit artifact.",
            f"Narrative family: {family.id}; setting family: {family.setting_family.value}.",
            "Unaided solvers should struggle; appendix-assisted solvers should recover the answer.",
        ],
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
            "When the pairing sheet was recovered, {label}'s {noun} stood at {value}.",
            "A witness who checked the roster left {label} with a {value} {noun}.",
            "In the earlier pairing note, {label} carried a {value} {noun}.",
            "Even the damaged roster still marked {label}'s {noun} as {value}.",
            "On the sealed worksheet, clerks wrote {value} beside {label}'s {noun}.",
            "The review panel confirmed that {label}'s {noun} remained {value}.",
        ),
        "temporal": (
            "Clocked entries put {label}'s {noun} at {value}.",
            "After the timesheet review, {label}'s {noun} stayed {value}.",
            "A clock-backed entry listed {label}'s {noun} as {value}.",
            "The sequence sheet showed {label}'s {noun} as {value}.",
            "Reconciled timing notes kept {label}'s {noun} at {value}.",
            "At the timed audit, {label}'s {noun} was still {value}.",
        ),
        "causal": (
            "Instruments tracing {label}'s action left the {noun} {value}.",
            "The {noun} that followed {label} registered as {value}.",
            "Downstream checks tied {label} to a {value} {noun}.",
            "When {label} acted, the {noun} came back {value}.",
            "Causal review marked {label}'s {noun} {value}.",
            "The effect chain after {label}'s step showed a {value} {noun}.",
        ),
        "spatial": (
            "Door and route checks placed {label}'s {noun} at {value}.",
            "A movement sketch marked {label}'s {noun} as {value}.",
            "Location review left {label}'s {noun} {value}.",
            "Witnesses in the corridor put {label}'s {noun} at {value}.",
            "The route ledger tied {label}'s {noun} to {value}.",
            "At the map table, {label}'s {noun} remained {value}.",
        ),
        "sequence": (
            "In the ordered log, {label}'s {noun} appeared as {value}.",
            "Sequence notes placed {label}'s {noun} at {value}.",
            "Reconstruction kept {label}'s {noun} at {value}.",
            "The ordered sheet showed {label}'s {noun} as {value}.",
            "At sequence review, {label}'s {noun} stayed {value}.",
            "Later collation still listed {label}'s {noun} as {value}.",
        ),
        "protocol": (
            "Token and seal checks left {label}'s {noun} at {value}.",
            "A close photograph of the token set {label}'s {noun} to {value}.",
            "Inventory counted {label}'s {noun} as {value}.",
            "The sealed check showed {label}'s {noun} as {value}.",
            "At final count, {label}'s {noun} remained {value}.",
            "Protocol clerks recorded {label}'s {noun} as {value}.",
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
    "checksum_after_cycles",
    "family_for_seed",
    "iterated_checksum",
]
