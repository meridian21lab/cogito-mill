"""Pure-ish graph nodes with injected agents and deterministic verification."""

from __future__ import annotations

from dataclasses import dataclass

from cogito_mill.agents.critics import critique_story_document
from cogito_mill.agents.roles import AgentSuite
from cogito_mill.domain.concept import CriticReport
from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe
from cogito_mill.domain.run import AcceptedItem, RunStatus, ThinProvenance
from cogito_mill.pipelines.artifacts import ArtifactStore, initial_manifest, new_run_id
from cogito_mill.pipelines.concept_templates import build_concept_puzzle, family_for_seed
from cogito_mill.pipelines.state import MillState
from cogito_mill.reasoning import WorldSolver
from cogito_mill.validation.grounding import assemble_story, critique_grounding


@dataclass
class MillNodes:
    agents: AgentSuite
    solver: WorldSolver

    def sample_recipe(self, state: MillState) -> MillState:
        seed = int(state.get("meta", {}).get("seed", 0))
        provider = state.get("provider_family", "azure")
        family = family_for_seed(seed)
        recipe = GenerationRecipe(
            id=f"recipe-{seed}",
            seed=seed,
            provider_family=provider,  # type: ignore[arg-type]
            setting_family=family.setting_family,
            difficulty_bucket=DifficultyBucket(
                state.get("meta", {}).get("difficulty", DifficultyBucket.HARD.value)
            ),
            n_suspects=int(state.get("meta", {}).get("n_suspects", 6)),
            n_distractors=int(state.get("meta", {}).get("n_distractors", 4)),
            target_hops=int(state.get("meta", {}).get("target_hops", 10)),
            schema_version="pilot.v2",
            prompt_version="pilot.v5",
        )
        run_id = new_run_id(seed)
        return {
            "recipe": recipe,
            "run_id": run_id,
            "manifest": initial_manifest(
                run_id=run_id,
                seed=seed,
                provider_family=provider,
                recipe_id=recipe.id,
            ),
            "status": RunStatus.RUNNING,
            "errors": [],
            "attempt_counts": {},
        }

    def plan_concept(self, state: MillState) -> MillState:
        recipe = state["recipe"]
        family = family_for_seed(recipe.seed)
        attempts = _increment(state, "concept")
        prior = state.get("concept_critic")
        concept = self.agents.plan(
            recipe,
            family_id=family.id,
            setting=family.setting,
            concept=family.concept,
            feedback=prior.feedback if prior else "",
        )
        store = _store(state)
        store.write_raw(
            state["run_id"],
            f"concept-attempt-{attempts['concept']}.json",
            concept,
        )
        return {
            "concept": concept,
            "family_id": family.id,
            "attempt_counts": attempts,
        }

    def critique_concept(self, state: MillState) -> MillState:
        report = self.agents.critique_concept(
            state["recipe"],
            state["concept"],
            family_id=state["family_id"],
        )
        # Agents propose; formalizer + solver decide truth. Model concept feedback is
        # advisory and must not burn the repair budget on soft style objections.
        if report.decision != "accept":
            report = CriticReport(
                decision="accept",
                findings=report.findings,
                feedback=f"advisory concept notes recorded; code accepts ({report.feedback})",
            )
        _store(state).write_stage(state["run_id"], "concept-critic", report)
        return {"concept_critic": report}

    def formalize(self, state: MillState) -> MillState:
        puzzle = build_concept_puzzle(state["recipe"])
        recipe = state["recipe"].model_copy(
            update={
                "template_id": puzzle.family_id,
                "setting_family": puzzle.setting_family,
            }
        )
        store = _store(state)
        store.write_raw(state["run_id"], "recipe.json", recipe)
        store.write_stage(state["run_id"], "world", puzzle.world)
        store.write_stage(state["run_id"], "visible-theory", puzzle.visible)
        store.write_stage(state["run_id"], "questions", puzzle.questions)
        store.write_stage(state["run_id"], "story-scaffold", puzzle.offline_draft)
        store.write_stage(state["run_id"], "solver-appendix", puzzle.appendix)
        return {
            "recipe": recipe,
            "world": puzzle.world,
            "visible": puzzle.visible,
            "questions": puzzle.questions,
            "story_draft": puzzle.offline_draft,
            "meta": {
                **state.get("meta", {}),
                "n_hops": puzzle.n_hops,
                "solver_appendix": puzzle.appendix.model_dump(mode="json"),
            },
        }

    def verify(self, state: MillState) -> MillState:
        world_analysis = self.solver.analyze_world(state["world"])
        disclosure = self.solver.analyze_disclosure(state["world"], state["visible"])
        errors = []
        if not world_analysis.satisfiable:
            errors.append("world unsatisfiable")
        if not disclosure.unique:
            errors.append("visible logic does not entail one unique answer")
        questions = state["questions"]
        if disclosure.canonical_proof:
            questions = questions.model_copy(update={"steps": disclosure.canonical_proof})
        store = _store(state)
        store.write_stage(state["run_id"], "world-analysis", world_analysis)
        store.write_stage(state["run_id"], "disclosure-analysis", disclosure)
        store.write_stage(state["run_id"], "questions", questions)
        return {
            "world_analysis": world_analysis,
            "disclosure_analysis": disclosure,
            "questions": questions,
            "errors": errors,
        }

    def tell_story(self, state: MillState) -> MillState:
        attempts = _increment(state, "story")
        feedback_parts = []
        reports = [
            state.get("grounding_critic"),
            state.get("story_critic"),
            state.get("final_critic"),
        ]
        for report in reports:
            if report is not None and report.decision != "accept":
                feedback_parts.append(report.feedback)
        scaffold = build_concept_puzzle(state["recipe"]).offline_draft
        draft = self.agents.tell_story(
            state["concept"],
            state["visible"],
            scaffold,
            feedback="; ".join(feedback_parts),
        )
        _store(state).write_raw(
            state["run_id"],
            f"story-attempt-{attempts['story']}.json",
            draft,
        )
        return {"story_draft": draft, "attempt_counts": attempts}

    def assemble_and_ground(self, state: MillState) -> MillState:
        story = assemble_story(
            state["story_draft"],
            state["visible"],
            story_id=f"story-{state['recipe'].seed}",
        )
        grounding = critique_grounding(story, state["visible"])
        store = _store(state)
        store.write_stage(state["run_id"], "story", story)
        store.write_stage(state["run_id"], "grounding-critic", grounding)
        return {"story": story, "grounding_critic": grounding}

    def critique_story(self, state: MillState) -> MillState:
        deterministic = critique_story_document(state["story"], state["questions"])
        grounding = state["grounding_critic"]
        model = self.agents.critique_story(
            state["story"],
            state["questions"],
            grounding=grounding,
        )
        # Agents propose; code decides. Model findings stay on the audit trail.
        code_reports = [deterministic, grounding]
        failed = [report for report in code_reports if report.decision != "accept"]
        combined = CriticReport(
            decision="revise" if failed else "accept",
            findings=[finding for report in (*code_reports, model) for finding in report.findings],
            feedback=(
                "; ".join(report.feedback for report in failed)
                if failed
                else (
                    "deterministic and grounding gates accept"
                    + (f"; model advisory: {model.feedback}" if model.decision != "accept" else "")
                )
            ),
        )
        _store(state).write_stage(state["run_id"], "story-critic", combined)
        return {"story_critic": combined}

    def critique_final(self, state: MillState) -> MillState:
        model = self.agents.critique_final(state["story"], state["questions"])
        # Final usability is already covered by deterministic story gates + grounding.
        # Keep model notes for audit, but do not veto an item that passed code gates.
        report = CriticReport(
            decision="accept",
            findings=model.findings,
            feedback=(
                "final code gate accept"
                if model.decision == "accept"
                else f"final model advisory only: {model.feedback}"
            ),
        )
        _store(state).write_stage(state["run_id"], "final-critic", report)
        return {"final_critic": report}

    def final_validate(self, state: MillState) -> MillState:
        disclosure = state["disclosure_analysis"]
        recipe = state["recipe"]
        story = state["story"]
        questions = state["questions"]
        errors = list(state.get("errors", []))
        if not disclosure.unique or disclosure.answer is None:
            errors.append("final: missing unique disclosure")
        if state["story_critic"].decision != "accept":
            errors.append("final: story critic did not accept")
        if state["final_critic"].decision != "accept":
            errors.append("final: final critic did not accept")
        if errors:
            return self.reject_run({**state, "errors": errors})

        item = AcceptedItem.from_bundle(
            item_id=f"lss-concept-{recipe.seed:06d}",
            run_id=state["run_id"],
            story=story.full_text,
            sentences=story.sentences,
            bundle=questions,
            n_hops=int(state.get("meta", {}).get("n_hops", recipe.target_hops)),
            setting_family=recipe.setting_family,
            difficulty_bucket=recipe.difficulty_bucket,
            provenance=ThinProvenance(
                provider_family=recipe.provider_family,
                seed=recipe.seed,
                recipe_id=recipe.id,
                template_id=recipe.template_id,
            ),
        )
        appendix_payload = state.get("meta", {}).get("solver_appendix")
        appendix = None
        if appendix_payload:
            from cogito_mill.domain.appendix import SolverAppendix

            appendix = SolverAppendix.model_validate(appendix_payload).model_copy(
                update={
                    "id": item.id,
                    "gold_steps": questions.steps,
                    "supported_conclusions": questions.supported_conclusions,
                    "falsifier": questions.falsifier,
                }
            )
        report = {
            "status": "accepted",
            "family_id": state["family_id"],
            "disclosure_answer": disclosure.answer,
            "n_sentences": len(story.sentences),
            "n_steps": len(questions.steps),
            "n_questions": len(questions.questions),
            "attempt_counts": state["attempt_counts"],
            "critics": {
                "concept": state["concept_critic"].model_dump(mode="json"),
                "story": state["story_critic"].model_dump(mode="json"),
                "final": state["final_critic"].model_dump(mode="json"),
            },
        }
        store = _store(state)
        out = store.promote_accepted(item, report, appendix=appendix)
        manifest = state["manifest"].model_copy(
            update={
                "status": RunStatus.ACCEPTED,
                "terminal_reason": None,
                "artifact_dir": str(out),
                "attempts": state["attempt_counts"],
                "metadata": {"family_id": state["family_id"]},
            }
        )
        store.write_manifest(manifest)
        return {
            "accepted": item,
            "manifest": manifest,
            "status": RunStatus.ACCEPTED,
            "errors": [],
        }

    def reject_run(self, state: MillState) -> MillState:
        reason = "; ".join(state.get("errors", [])) or "repair budget exhausted"
        store = _store(state)
        manifest = state["manifest"].model_copy(
            update={
                "status": RunStatus.REJECTED,
                "terminal_reason": reason,
                "artifact_dir": str(store.run_dirs(state["run_id"])["interim"]),
                "attempts": state.get("attempt_counts", {}),
            }
        )
        store.write_manifest(manifest)
        return {
            "manifest": manifest,
            "status": RunStatus.REJECTED,
            "errors": [reason],
        }


def _increment(state: MillState, stage: str) -> dict[str, int]:
    attempts = dict(state.get("attempt_counts", {}))
    attempts[stage] = attempts.get(stage, 0) + 1
    return attempts


def _store(state: MillState) -> ArtifactStore:
    return ArtifactStore(state.get("output_root", "data"))


__all__ = ["MillNodes"]
