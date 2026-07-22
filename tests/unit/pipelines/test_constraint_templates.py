"""Relational constraint-world mechanism tests."""

from __future__ import annotations

from cogito_mill.agents.critics import critique_story_document, formulaic_hits
from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe
from cogito_mill.pipelines.concept_templates import build_concept_puzzle, family_for_seed
from cogito_mill.reasoning.constraints import TargetTuple, target_tuples
from cogito_mill.reasoning.solver import WorldSolver
from cogito_mill.validation.grounding import assemble_story, critique_grounding


def _recipe(seed: int) -> GenerationRecipe:
    family = family_for_seed(seed)
    return GenerationRecipe(
        id=f"recipe-{seed}",
        seed=seed,
        setting_family=family.setting_family,
        difficulty_bucket=DifficultyBucket.VERY_HARD,
        n_suspects=6,
        n_distractors=6,
        target_hops=10,
        schema_version="pilot.v2",
        prompt_version="pilot.v6",
    )


def test_constraint_world_has_unique_solver_derived_target() -> None:
    for seed in range(15000, 15006):
        puzzle = build_concept_puzzle(_recipe(seed))
        disclosure = WorldSolver().analyze_disclosure(puzzle.world, puzzle.visible)

        assert disclosure.unique
        assert disclosure.answer == puzzle.world.answer_entity
        assert puzzle.visible.constraints is not None
        assert puzzle.visible.logic is None
        assert puzzle.appendix.mechanism == "relational_constraint_world"
        assert 10 <= len(puzzle.visible.constraints.clues) <= 30
        target_place = next(
            question.gold_answer
            for question in puzzle.questions.questions
            if question.id == "q_target_place"
        )
        target_time = next(
            question.gold_answer
            for question in puzzle.questions.questions
            if question.id == "q_target_time"
        )
        assert target_tuples(puzzle.visible.constraints) == [
            TargetTuple(
                person=puzzle.world.answer_entity,
                place=target_place,
                time=target_time,
            )
        ]
        assert not any(
            set(clue.axes) == {"person", "object"} for clue in puzzle.visible.constraints.clues
        )


def test_every_constraint_clue_is_target_necessary() -> None:
    puzzle = build_concept_puzzle(_recipe(15003))
    assert puzzle.visible.constraints is not None
    theory = puzzle.visible.constraints
    expected = target_tuples(theory)
    assert len(expected) == 1

    for clue in theory.clues:
        reduced = theory.model_copy(
            update={"clues": [item for item in theory.clues if item.id != clue.id]}
        )
        assert target_tuples(reduced) != expected, clue.id


def test_target_depends_on_object_place_and_time_axes() -> None:
    puzzle = build_concept_puzzle(_recipe(15004))
    assert puzzle.visible.constraints is not None
    theory = puzzle.visible.constraints
    expected = target_tuples(theory)
    assert len(expected) == 1

    for axis in ("object", "place", "time"):
        reduced = theory.model_copy(
            update={"clues": [clue for clue in theory.clues if axis not in clue.axes]}
        )
        assert target_tuples(reduced) != expected, axis


def test_constraint_appendix_carries_machine_certificate() -> None:
    puzzle = build_concept_puzzle(_recipe(15005))
    appendix = puzzle.appendix
    text = appendix.to_solver_text()

    assert appendix.constraint_clues
    assert len(appendix.constraint_solution) == 6
    assert "Relational constraints:" in text
    assert "Verified assignment:" in text
    assert appendix.incident["target_object"]
    sizes = appendix.incident["candidate_target_core_sizes"]
    assert len(appendix.constraint_clues) == max(sizes.values())


def test_offline_constraint_story_passes_item_gates() -> None:
    puzzle = build_concept_puzzle(_recipe(15000))
    story = assemble_story(puzzle.offline_draft, puzzle.visible, story_id="story-15000")

    assert critique_grounding(story, puzzle.visible).decision == "accept"
    assert critique_story_document(story, puzzle.questions).decision == "accept"
    assert not formulaic_hits(story.full_text)
    assert puzzle.questions.gold_answer not in story.full_text
