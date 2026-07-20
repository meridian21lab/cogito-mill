"""Run status, manifests, and release projections."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from cogito_mill.domain.narrative import Sentence
from cogito_mill.domain.questions import CounterfactualTask, FalsifierTask, QuestionBundle
from cogito_mill.domain.reasoning import DeductionStep
from cogito_mill.domain.recipe import DifficultyBucket, SettingFamily


class RunStatus(StrEnum):
    RUNNING = "running"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


class ThinProvenance(BaseModel):
    provider_family: str
    seed: int
    recipe_id: str
    writer_deployment: str | None = None
    judge_deployment: str | None = None
    template_id: str | None = None


class RunManifest(BaseModel):
    run_id: str
    status: RunStatus
    seed: int
    provider_family: str
    recipe_id: str
    schema_version: str = "pilot.v0"
    terminal_reason: str | None = None
    artifact_dir: str | None = None
    content_hashes: dict[str, str] = Field(default_factory=dict)
    attempts: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AcceptedItem(BaseModel):
    id: str
    schema_version: str = "pilot.v0"
    run_id: str
    story: str
    sentences: list[Sentence] = Field(default_factory=list)
    question: str
    gold_answer: str
    supported_conclusions: list[str] = Field(default_factory=list)
    gold_steps: list[DeductionStep] = Field(default_factory=list)
    counterfactual: CounterfactualTask | None = None
    falsifier: FalsifierTask | None = None
    n_hops: int
    setting_family: SettingFamily
    difficulty_bucket: DifficultyBucket
    provenance: ThinProvenance

    def to_hub_item(self) -> PilotHubItem:
        return PilotHubItem(
            id=self.id,
            story=self.story,
            question=self.question,
            gold_answer=self.gold_answer,
            n_hops=self.n_hops,
            setting_family=self.setting_family,
            difficulty_bucket=self.difficulty_bucket,
        )

    @classmethod
    def from_bundle(
        cls,
        *,
        item_id: str,
        run_id: str,
        story: str,
        sentences: list[Sentence],
        bundle: QuestionBundle,
        n_hops: int,
        setting_family: SettingFamily,
        difficulty_bucket: DifficultyBucket,
        provenance: ThinProvenance,
    ) -> AcceptedItem:
        return cls(
            id=item_id,
            run_id=run_id,
            story=story,
            sentences=sentences,
            question=bundle.main_question,
            gold_answer=bundle.gold_answer,
            supported_conclusions=bundle.supported_conclusions,
            gold_steps=bundle.steps,
            counterfactual=bundle.counterfactual,
            falsifier=bundle.falsifier,
            n_hops=n_hops,
            setting_family=setting_family,
            difficulty_bucket=difficulty_bucket,
            provenance=provenance,
        )


class PilotHubItem(BaseModel):
    id: str
    story: str
    question: str
    gold_answer: str
    n_hops: int
    setting_family: SettingFamily
    difficulty_bucket: DifficultyBucket
