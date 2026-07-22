"""Generation recipes and difficulty metadata."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SettingFamily(StrEnum):
    DETECTIVE = "detective"
    DOMESTIC = "domestic"
    WORKPLACE = "workplace"
    EXPEDITION = "expedition"
    HISTORICAL = "historical"
    SPECULATIVE = "speculative"


class DifficultyBucket(StrEnum):
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"


class GenerationRecipe(BaseModel):
    """Sampled constraints for one generation run."""

    id: str
    seed: int
    provider_family: Literal["azure", "glm"] = "azure"
    setting_family: SettingFamily
    difficulty_bucket: DifficultyBucket = DifficultyBucket.HARD
    target_hops: int = Field(default=5, ge=3, le=12)
    n_suspects: int = Field(default=4, ge=3, le=8)
    n_distractors: int = Field(default=4, ge=1, le=12)
    require_relational: bool = True
    require_temporal: bool = True
    require_causal: bool = True
    template_id: str = "access_timeline_v1"
    schema_version: str = "pilot.v0"
    prompt_version: str = "pilot.v0"
    max_concept_repairs: int = 2
    max_stage_repairs: int = 2
    forbidden_shortcuts: list[str] = Field(
        default_factory=lambda: [
            "genre_trope_answer",
            "name_equals_role",
            "answer_in_first_paragraph",
        ]
    )

    @field_validator("id")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("id must be non-empty")
        return value
