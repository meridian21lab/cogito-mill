"""Concept portfolio and solver-appendix tests."""

from __future__ import annotations

import re

from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe
from cogito_mill.pipelines.concept_templates import (
    FAMILIES,
    build_concept_puzzle,
    family_for_seed,
    iterated_checksum,
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
        prompt_version="pilot.v3",
    )


def test_iterated_checksum_carries_state_across_all_five_cycles() -> None:
    result = iterated_checksum(
        (3, 5, 5, 2, 2, 1),
        (13, 7, 3, 11, 2, 5),
        start_value=12,
        modulus=97,
        cycle_count=5,
    )

    assert result == 19


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
    assert puzzle.appendix.checksum_params.cycle_count >= 97


def test_counterfactual_is_evidence_edit_not_checksum_retarget() -> None:
    puzzle = build_concept_puzzle(_recipe(1210))
    cf = next(q for q in puzzle.questions.questions if q.question_type == "counterfactual")
    assert "accepted checksum had been" not in cf.question
    assert "status had been" in cf.question
    assert puzzle.appendix.evidence_counterfactual is not None
    assert puzzle.appendix.evidence_counterfactual.fact_id.startswith("f_")


def test_appendix_includes_matrix_checkpoints_and_falsifier() -> None:
    puzzle = build_concept_puzzle(_recipe(1226))
    appendix = puzzle.appendix
    assert appendix.status_matrix
    assert appendix.candidate_checksums
    assert appendix.checkpoints
    assert appendix.falsifier is not None
    assert appendix.falsifier.minimal_evidence
    text = appendix.to_solver_text()
    assert "Status weights" in text
    assert "Candidate checksums" in text


def test_puzzle_has_unique_disclosure() -> None:
    puzzle = build_concept_puzzle(_recipe(1202))
    solver = WorldSolver()
    world = solver.analyze_world(puzzle.world)
    disclosure = solver.analyze_disclosure(puzzle.world, puzzle.visible)
    assert world.satisfiable
    assert disclosure.unique
    assert disclosure.answer == puzzle.world.answer_entity


def test_weight_facts_are_not_six_separate_ledger_lines() -> None:
    puzzle = build_concept_puzzle(_recipe(1202))
    weight_facts = [fact for fact in puzzle.visible.facts if fact.id.startswith("f_weight_")]
    assert weight_facts == []
    assert any(fact.id == "f_status_weights" for fact in puzzle.visible.facts)


def test_consecutive_seeds_cover_all_families() -> None:
    from collections import Counter

    families = [family_for_seed(seed).id for seed in range(10000, 10012)]
    assert len(set(families)) == len(FAMILIES)
    counts = Counter(families)
    assert max(counts.values()) <= 2
