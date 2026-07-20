"""Narrative artifacts."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class Sentence(BaseModel):
    id: str
    text: str


class SceneDraft(BaseModel):
    id: str
    title: str
    obligated_fact_ids: list[str] = Field(default_factory=list)
    prose: str = ""


class StoryDocument(BaseModel):
    id: str
    title: str
    scenes: list[SceneDraft]
    sentences: list[Sentence]
    full_text: str

    @model_validator(mode="after")
    def _nonempty_story(self) -> StoryDocument:
        if not self.full_text.strip():
            raise ValueError("story full_text must be non-empty")
        if not self.sentences:
            raise ValueError("story must have sentence IDs")
        return self
