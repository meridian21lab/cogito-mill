"""Question bundle for an accepted item."""

from __future__ import annotations

from pydantic import BaseModel, Field

from cogito_mill.domain.reasoning import DeductionStep


class CounterfactualTask(BaseModel):
    question: str
    answer: str
    intervention: str


class FalsifierTask(BaseModel):
    hypothesis: str
    minimal_evidence: list[str] = Field(default_factory=list)


class QuestionBundle(BaseModel):
    main_question: str
    gold_answer: str
    supported_conclusions: list[str] = Field(default_factory=list)
    steps: list[DeductionStep] = Field(default_factory=list)
    counterfactual: CounterfactualTask | None = None
    falsifier: FalsifierTask | None = None
