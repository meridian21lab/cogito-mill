"""Deterministic world and disclosure analysis reports."""

from __future__ import annotations

from pydantic import BaseModel, Field

from cogito_mill.domain.reasoning import DeductionStep


class WorldAnalysis(BaseModel):
    satisfiable: bool
    target_truth: str | None = None
    derived_facts: list[str] = Field(default_factory=list)
    causal_trace: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)


class DisclosureAnalysis(BaseModel):
    answerable: bool
    unique: bool
    answer: str | None = None
    alternative_answers: list[str] = Field(default_factory=list)
    minimal_support: list[str] = Field(default_factory=list)
    canonical_proof: list[DeductionStep] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CounterfactualAnalysis(BaseModel):
    intervention_id: str
    answer: str
    derived_facts: list[str] = Field(default_factory=list)
    causal_trace: list[str] = Field(default_factory=list)


class FalsificationAnalysis(BaseModel):
    hypothesis: str
    status: str
    minimal_contradictory_set: list[str] = Field(default_factory=list)
