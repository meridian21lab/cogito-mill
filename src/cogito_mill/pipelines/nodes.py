"""Graph node functions for the pilot mill."""

from __future__ import annotations

from cogito_mill.domain.reasoning import DeductionStep
from cogito_mill.domain.recipe import (
    DifficultyBucket,
    GenerationRecipe,
    SettingFamily,
)
from cogito_mill.domain.run import AcceptedItem, RunStatus, ThinProvenance
from cogito_mill.pipelines.artifacts import ArtifactStore, initial_manifest, new_run_id
from cogito_mill.pipelines.state import MillState
from cogito_mill.pipelines.templates import build_access_timeline
from cogito_mill.reasoning import WorldSolver

_SETTINGS = list(SettingFamily)


def sample_recipe(state: MillState) -> MillState:
    seed = int(state.get("meta", {}).get("seed", 0))
    provider = state.get("provider_family", "azure")
    difficulty = DifficultyBucket(
        state.get("meta", {}).get("difficulty", DifficultyBucket.HARD.value)
    )
    n_suspects = int(state.get("meta", {}).get("n_suspects", 4))
    n_distractors = int(state.get("meta", {}).get("n_distractors", 4))
    setting = _SETTINGS[seed % len(_SETTINGS)]
    recipe = GenerationRecipe(
        id=f"recipe-{seed}",
        seed=seed,
        provider_family=provider,  # type: ignore[arg-type]
        setting_family=setting,
        difficulty_bucket=difficulty,
        n_suspects=n_suspects,
        n_distractors=n_distractors,
        target_hops=int(state.get("meta", {}).get("target_hops", 5)),
    )
    run_id = new_run_id(seed)
    manifest = initial_manifest(
        run_id=run_id,
        seed=seed,
        provider_family=provider,
        recipe_id=recipe.id,
    )
    return {
        **state,
        "recipe": recipe,
        "run_id": run_id,
        "manifest": manifest,
        "status": RunStatus.RUNNING,
        "errors": [],
    }


def formalize_and_disclose(state: MillState) -> MillState:
    recipe = state["recipe"]
    bundle = build_access_timeline(recipe)
    solver = WorldSolver()
    world_analysis = solver.analyze_world(bundle.world)
    disclosure = solver.analyze_disclosure(bundle.world, bundle.visible)
    errors = list(state.get("errors", []))
    if not world_analysis.satisfiable:
        errors.append("world unsatisfiable")
    if not disclosure.unique:
        errors.append("disclosure not unique")
    # attach solver proof into questions
    questions = bundle.questions
    if disclosure.canonical_proof:
        questions = questions.model_copy(update={"steps": disclosure.canonical_proof})
    store = ArtifactStore(state.get("output_root", "data"))
    run_id = state["run_id"]
    store.write_raw(run_id, "recipe.json", recipe)
    store.write_stage(run_id, "world", bundle.world)
    store.write_stage(run_id, "world-analysis", world_analysis)
    store.write_stage(run_id, "visible-theory", bundle.visible)
    store.write_stage(run_id, "disclosure-analysis", disclosure)
    store.write_stage(run_id, "story", bundle.story)
    store.write_stage(run_id, "questions", questions)
    return {
        **state,
        "world": bundle.world,
        "visible": bundle.visible,
        "story": bundle.story,
        "questions": questions,
        "world_analysis": world_analysis,
        "disclosure_analysis": disclosure,
        "errors": errors,
        "meta": {
            **state.get("meta", {}),
            "n_hops": bundle.n_hops,
        },
    }


def final_validate(state: MillState) -> MillState:
    errors = list(state.get("errors", []))
    disclosure = state.get("disclosure_analysis")
    story = state.get("story")
    questions = state.get("questions")
    recipe = state["recipe"]
    if disclosure is None or not disclosure.unique or disclosure.answer is None:
        errors.append("final: missing unique disclosure")
    if story is None or not story.full_text.strip():
        errors.append("final: empty story")
    if questions is None or not questions.gold_answer:
        errors.append("final: missing gold answer")

    store = ArtifactStore(state.get("output_root", "data"))
    run_id = state["run_id"]
    manifest = state["manifest"]

    if errors:
        manifest = manifest.model_copy(
            update={
                "status": RunStatus.REJECTED,
                "terminal_reason": "; ".join(errors),
                "artifact_dir": str(store.run_dirs(run_id)["interim"]),
            }
        )
        store.write_manifest(manifest)
        return {
            **state,
            "errors": errors,
            "manifest": manifest,
            "status": RunStatus.REJECTED,
        }

    assert disclosure is not None and questions is not None and story is not None
    # Ensure gold answer label matches entity
    answer_entity = disclosure.answer
    label = next(e.label for e in state["world"].entities if e.id == answer_entity)
    if questions.gold_answer != label:
        questions = questions.model_copy(update={"gold_answer": label})

    item_id = f"lss-pilot-{recipe.seed:06d}"
    provenance = ThinProvenance(
        provider_family=recipe.provider_family,
        seed=recipe.seed,
        recipe_id=recipe.id,
        template_id=recipe.template_id,
    )
    steps: list[DeductionStep] = list(questions.steps)
    item = AcceptedItem(
        id=item_id,
        run_id=run_id,
        story=story.full_text,
        sentences=story.sentences,
        question=questions.main_question,
        gold_answer=questions.gold_answer,
        supported_conclusions=questions.supported_conclusions,
        gold_steps=steps,
        counterfactual=questions.counterfactual,
        falsifier=questions.falsifier,
        n_hops=int(state.get("meta", {}).get("n_hops", recipe.target_hops)),
        setting_family=recipe.setting_family,
        difficulty_bucket=recipe.difficulty_bucket,
        provenance=provenance,
    )
    report = {
        "status": "accepted",
        "disclosure_answer": disclosure.answer,
        "n_sentences": len(story.sentences),
        "n_steps": len(steps),
    }
    out = store.promote_accepted(item, report)
    manifest = manifest.model_copy(
        update={
            "status": RunStatus.ACCEPTED,
            "terminal_reason": None,
            "artifact_dir": str(out),
        }
    )
    store.write_manifest(manifest)
    return {
        **state,
        "questions": questions,
        "accepted": item,
        "manifest": manifest,
        "status": RunStatus.ACCEPTED,
        "errors": [],
    }
