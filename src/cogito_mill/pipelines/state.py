"""LangGraph mill state."""

from __future__ import annotations

from typing import Any, TypedDict

from cogito_mill.domain.concept import ConceptBrief, CriticReport
from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.narrative import StoryDocument, StoryDraft
from cogito_mill.domain.questions import QuestionBundle
from cogito_mill.domain.recipe import GenerationRecipe
from cogito_mill.domain.run import AcceptedItem, RunManifest, RunStatus
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning.reports import DisclosureAnalysis, WorldAnalysis


class MillState(TypedDict, total=False):
    recipe: GenerationRecipe
    concept: ConceptBrief
    concept_critic: CriticReport
    family_id: str
    world: WorldSpec
    visible: VisibleTheory
    story_draft: StoryDraft
    story: StoryDocument
    questions: QuestionBundle
    world_analysis: WorldAnalysis
    disclosure_analysis: DisclosureAnalysis
    story_critic: CriticReport
    grounding_critic: CriticReport
    final_critic: CriticReport
    accepted: AcceptedItem
    manifest: RunManifest
    status: RunStatus
    errors: list[str]
    run_id: str
    output_root: str
    provider_family: str
    meta: dict[str, Any]
    attempt_counts: dict[str, int]
