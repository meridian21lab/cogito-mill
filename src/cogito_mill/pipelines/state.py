"""LangGraph mill state."""

from __future__ import annotations

from typing import Any, TypedDict

from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.narrative import StoryDocument
from cogito_mill.domain.questions import QuestionBundle
from cogito_mill.domain.recipe import GenerationRecipe
from cogito_mill.domain.run import AcceptedItem, RunManifest, RunStatus
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning.reports import DisclosureAnalysis, WorldAnalysis


class MillState(TypedDict, total=False):
    recipe: GenerationRecipe
    world: WorldSpec
    visible: VisibleTheory
    story: StoryDocument
    questions: QuestionBundle
    world_analysis: WorldAnalysis
    disclosure_analysis: DisclosureAnalysis
    accepted: AcceptedItem
    manifest: RunManifest
    status: RunStatus
    errors: list[str]
    run_id: str
    output_root: str
    provider_family: str
    meta: dict[str, Any]
