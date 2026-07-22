"""Explicit graph role and bounded-repair integration tests."""

from pathlib import Path

from cogito_mill.agents.roles import OfflineAgentSuite
from cogito_mill.domain.concept import ConceptBrief, CriticFinding, CriticReport
from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.narrative import StoryDocument, StoryDraft
from cogito_mill.domain.questions import QuestionBundle
from cogito_mill.domain.recipe import GenerationRecipe
from cogito_mill.pipelines.runner import generate_one


class RepairingAgents(OfflineAgentSuite):
    def __init__(self) -> None:
        self.concept_reviews = 0
        self.story_reviews = 0
        self.final_reviews = 0

    def critique_concept(
        self,
        recipe: GenerationRecipe,
        concept: ConceptBrief,
        *,
        family_id: str,
    ) -> CriticReport:
        self.concept_reviews += 1
        return _decision("revise")

    def tell_story(
        self,
        concept: ConceptBrief,
        visible: VisibleTheory,
        scaffold: StoryDraft,
        *,
        feedback: str = "",
    ) -> StoryDraft:
        return scaffold

    def critique_story(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
        *,
        grounding: CriticReport,
    ) -> CriticReport:
        self.story_reviews += 1
        return _decision("revise")

    def critique_final(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
    ) -> CriticReport:
        self.final_reviews += 1
        return _decision("revise")


def _decision(decision: str) -> CriticReport:
    return CriticReport(
        decision=decision,  # type: ignore[arg-type]
        findings=[
            CriticFinding(
                gate="scripted",
                passed=decision == "accept",
                detail=decision,
            )
        ],
        feedback=decision,
    )


def test_model_critics_are_advisory_when_code_gates_pass(tmp_path: Path) -> None:
    """Agents propose; deterministic story/grounding gates decide acceptance."""
    agents = RepairingAgents()

    result = generate_one(
        seed=84,
        output_root=str(tmp_path),
        n_suspects=6,
        agents=agents,
    )

    assert result["status"] == "accepted"
    assert agents.concept_reviews == 1
    assert agents.story_reviews == 1
    assert agents.final_reviews == 1
    manifest = result["accepted"]
    assert manifest.provenance.template_id
    assert (tmp_path / "raw" / result["run_id"] / "concept-attempt-1.json").exists()
    assert not (tmp_path / "raw" / result["run_id"] / "concept-attempt-2.json").exists()
    assert (tmp_path / "raw" / result["run_id"] / "story-attempt-1.json").exists()
    assert not (tmp_path / "raw" / result["run_id"] / "story-attempt-2.json").exists()
