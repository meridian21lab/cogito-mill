"""Timeline portfolio and solver-appendix tests."""

from __future__ import annotations

import re

from cogito_mill.agents.critics import formulaic_hits
from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe
from cogito_mill.pipelines.concept_templates import (
    FAMILIES,
    build_concept_puzzle,
    family_for_seed,
    has_opportunity,
    minutes_to_clock,
    travel_matrix,
)
from cogito_mill.reasoning.solver import WorldSolver


def _recipe(seed: int, n_suspects: int = 5) -> GenerationRecipe:
    family = family_for_seed(seed)
    return GenerationRecipe(
        id=f"recipe-{seed}",
        seed=seed,
        setting_family=family.setting_family,
        difficulty_bucket=DifficultyBucket.VERY_HARD,
        n_suspects=n_suspects,
        n_distractors=4,
        target_hops=10,
        schema_version="pilot.v2",
        prompt_version="pilot.v4",
    )


def test_names_are_unique_without_numeric_suffixes() -> None:
    for seed in range(1200, 1230):
        puzzle = build_concept_puzzle(_recipe(seed))
        labels = [entity.label for entity in puzzle.world.entities]
        assert len(labels) == len(set(labels))
        assert all(not re.search(r"-\d+$", label) for label in labels)


def test_setting_family_matches_narrative_family() -> None:
    for seed in (1202, 1210, 1213, 1221, 1226, 1232):
        family = family_for_seed(seed)
        puzzle = build_concept_puzzle(_recipe(seed))
        assert puzzle.setting_family == family.setting_family
        assert family.setting in puzzle.offline_draft.opening


def test_structural_hops_are_human_scale() -> None:
    puzzle = build_concept_puzzle(_recipe(1213, n_suspects=5))
    assert 10 <= puzzle.n_hops <= 80
    assert puzzle.appendix.mechanism == "timeline_opportunity"


def test_counterfactual_is_evidence_edit_not_checksum_retarget() -> None:
    puzzle = build_concept_puzzle(_recipe(1210))
    cf = next(q for q in puzzle.questions.questions if q.question_type == "counterfactual")
    assert "accepted checksum had been" not in cf.question
    assert "status scale" not in puzzle.offline_draft.opening
    assert puzzle.appendix.evidence_counterfactual is not None


def test_appendix_includes_timelines_and_eliminations() -> None:
    puzzle = build_concept_puzzle(_recipe(1226))
    appendix = puzzle.appendix
    assert appendix.timelines
    assert appendix.opportunity
    assert appendix.eliminations
    text = appendix.to_solver_text()
    assert "Timelines" in text
    assert "Opportunity" in text


def test_puzzle_has_unique_disclosure() -> None:
    puzzle = build_concept_puzzle(_recipe(1202))
    solver = WorldSolver()
    world = solver.analyze_world(puzzle.world)
    disclosure = solver.analyze_disclosure(puzzle.world, puzzle.visible)
    assert world.satisfiable
    assert disclosure.unique
    assert disclosure.answer == puzzle.world.answer_entity


def test_scaffold_has_no_formulaic_ledger_language() -> None:
    for seed in range(10000, 10012):
        puzzle = build_concept_puzzle(_recipe(seed))
        text = puzzle.offline_draft.opening + " ".join(
            scene.prose for scene in puzzle.offline_draft.scenes
        )
        assert not formulaic_hits(text)


def test_consecutive_seeds_cover_all_families() -> None:
    from collections import Counter

    families = [family_for_seed(seed).id for seed in range(10000, 10012)]
    assert len(set(families)) == len(FAMILIES)
    counts = Counter(families)
    assert max(counts.values()) <= 2


def test_minutes_to_clock_formats() -> None:
    assert minutes_to_clock(14 * 60 + 30) == "2:30 PM"
    assert minutes_to_clock(9 * 60 + 5) == "9:05 AM"


def test_has_opportunity_blocks_overlap() -> None:
    from cogito_mill.pipelines.concept_templates import Segment

    family = family_for_seed(10000)
    travel = travel_matrix(family)
    segments = [
        Segment(family.places[1], 14 * 60 + 20, 15 * 60, "overlap", "f1"),
    ]
    assert not has_opportunity(
        segments,
        crime_place=family.crime_place,
        crime_start=14 * 60 + 30,
        crime_end=15 * 60,
        travel=travel,
    )
