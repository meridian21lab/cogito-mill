"""Connected custody-provenance mechanism tests."""

from __future__ import annotations

from cogito_mill.agents.critics import critique_story_document, formulaic_hits
from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe
from cogito_mill.pipelines.concept_templates import build_concept_puzzle, family_for_seed
from cogito_mill.reasoning.logic import goal_candidates
from cogito_mill.reasoning.solver import WorldSolver
from cogito_mill.validation.grounding import assemble_story, critique_grounding


def _recipe(seed: int, n_suspects: int = 5) -> GenerationRecipe:
    family = family_for_seed(seed)
    return GenerationRecipe(
        id=f"recipe-{seed}",
        seed=seed,
        setting_family=family.setting_family,
        difficulty_bucket=DifficultyBucket.VERY_HARD,
        n_suspects=n_suspects,
        n_distractors=6,
        target_hops=10,
        schema_version="pilot.v2",
        prompt_version="pilot.v5",
    )


def test_provenance_puzzle_has_unique_connected_disclosure() -> None:
    for seed in range(13000, 13006):
        puzzle = build_concept_puzzle(_recipe(seed))
        disclosure = WorldSolver().analyze_disclosure(puzzle.world, puzzle.visible)

        assert disclosure.unique
        assert disclosure.answer == puzzle.world.answer_entity
        assert puzzle.appendix.mechanism == "provenance_custody_dag"
        assert puzzle.n_hops >= 10
        assert not any(atom.predicate == "has_opportunity" for atom in puzzle.visible.logic.facts)
        assert set(puzzle.appendix.opportunity.values()) == {True}


def test_every_key_proof_clue_is_necessary() -> None:
    puzzle = build_concept_puzzle(_recipe(13003))
    assert puzzle.visible.logic is not None
    critical_ids = puzzle.appendix.incident["critical_fact_ids"]
    facts_by_id = {fact.id: fact for fact in puzzle.visible.facts}

    assert len(critical_ids) >= 10
    for fact_id in critical_ids:
        atom_key = facts_by_id[fact_id].formal.removeprefix("atom:")
        reduced = puzzle.visible.logic.model_copy(
            update={"facts": [atom for atom in puzzle.visible.logic.facts if atom.key != atom_key]}
        )
        survivors = goal_candidates(reduced, puzzle.world.candidate_answers)
        assert survivors != [puzzle.world.answer_entity], fact_id


def test_counterfactual_changes_only_final_recipient() -> None:
    puzzle = build_concept_puzzle(_recipe(13004))
    intervention = puzzle.appendix.evidence_counterfactual
    counterfactual = next(
        question
        for question in puzzle.questions.questions
        if question.question_type == "counterfactual"
    )

    assert intervention is not None
    assert intervention.fact_id == "f_event_21"
    assert counterfactual.gold_answer == intervention.answer_label
    assert counterfactual.gold_answer != puzzle.questions.gold_answer
    assert "every earlier handoff and contents transfer stayed fixed" in counterfactual.question


def test_appendix_exposes_auditable_state_trace() -> None:
    puzzle = build_concept_puzzle(_recipe(13005))
    states = puzzle.appendix.provenance_states
    text = puzzle.appendix.to_solver_text()

    assert len(states) == 22
    assert [state.step for state in states] == list(range(22))
    assert "Custody provenance:" in text
    assert "critical_fact_ids" in puzzle.appendix.incident
    assert puzzle.appendix.incident["final_step"] == 21


def test_offline_story_passes_item_gates_without_formula_ledger_or_answer_leak() -> None:
    puzzle = build_concept_puzzle(_recipe(13000))
    story = assemble_story(puzzle.offline_draft, puzzle.visible, story_id="story-13000")

    assert critique_grounding(story, puzzle.visible).decision == "accept"
    assert critique_story_document(story, puzzle.questions).decision == "accept"
    assert not formulaic_hits(story.full_text)
    assert puzzle.questions.gold_answer not in story.full_text


def test_v4_recipe_still_dispatches_to_frozen_timeline_mechanism() -> None:
    recipe = _recipe(12000).model_copy(update={"prompt_version": "pilot.v4"})
    puzzle = build_concept_puzzle(recipe)

    assert puzzle.appendix.mechanism == "timeline_opportunity"
