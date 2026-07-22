"""Serializable relational constraint worlds for narrative logic-grid puzzles."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ConstraintKind = Literal[
    "person_not_place",
    "person_not_time",
    "object_not_place",
    "object_not_time",
    "place_not_time",
    "person_before_person",
    "object_before_object",
    "place_before_place",
    "person_place_xor_time",
    "object_place_xor_time",
]


class ConstraintClue(BaseModel):
    id: str
    kind: ConstraintKind
    arguments: list[str]
    text: str
    axes: list[Literal["person", "object", "place", "time"]] = Field(default_factory=list)
    scene_id: str


class ConstraintTheory(BaseModel):
    """Visible constraints; hidden assignments are intentionally excluded."""

    people: list[str]
    objects: list[str]
    places: list[str]
    times: list[str]
    clues: list[ConstraintClue]
    target_object: str


__all__ = ["ConstraintClue", "ConstraintKind", "ConstraintTheory"]
