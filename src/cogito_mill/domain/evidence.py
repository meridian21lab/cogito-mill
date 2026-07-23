"""Visible evidence theory disclosed to the reader."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from cogito_mill.domain.constraints import ConstraintTheory
from cogito_mill.domain.logic import LogicTheory


class ClueChannel(StrEnum):
    STATEMENT = "statement"
    OBSERVATION = "observation"
    RECORD = "record"
    PHYSICAL_STATE = "physical_state"
    RULE_APPLICATION = "rule_application"


class VisibleFact(BaseModel):
    id: str
    text: str
    formal: str
    channel: ClueChannel
    role: str = "required"  # required | distractor | red_herring | context
    scene_id: str
    reveal_order: int
    sentence_ids: list[str] = Field(default_factory=list)


class VisibleTheory(BaseModel):
    id: str
    world_id: str
    facts: list[VisibleFact]
    hidden_fact_ids: list[str] = Field(default_factory=list)
    logic: LogicTheory | None = None
    constraints: ConstraintTheory | None = None
