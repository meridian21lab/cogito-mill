"""Typed deduction steps."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class InferenceType(StrEnum):
    LOOKUP = "lookup"
    ELIMINATION = "elimination"
    TEMPORAL_ORDER = "temporal_order"
    RELATION_COMPOSE = "relation_compose"
    CAUSAL_EFFECT = "causal_effect"
    CONTRADICTION = "contradiction"
    CONCLUSION = "conclusion"


class DeductionStep(BaseModel):
    id: str
    evidence_fact_ids: list[str] = Field(default_factory=list)
    evidence_sentence_ids: list[str] = Field(default_factory=list)
    prior_step_ids: list[str] = Field(default_factory=list)
    inference_type: InferenceType
    conclusion: str
    explanation: str = ""
