"""Question bundle for an accepted item."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from cogito_mill.domain.reasoning import DeductionStep


class CounterfactualTask(BaseModel):
    question: str
    answer: str
    intervention: str


class FalsifierTask(BaseModel):
    hypothesis: str
    minimal_evidence: list[str] = Field(default_factory=list)


class ScoredQuestion(BaseModel):
    """One scored reader-facing question with exact-match answer forms."""

    id: str
    question: str
    gold_answer: str
    gold_answer_variants: list[str] = Field(default_factory=list)
    question_type: Literal[
        "main",
        "intermediate",
        "counterfactual",
        "code",
        "scalar",
    ] = "main"

    @model_validator(mode="after")
    def _normalize_variants(self) -> ScoredQuestion:
        variants: list[str] = []
        for item in [self.gold_answer, *self.gold_answer_variants]:
            text = (item or "").strip()
            if text and text not in variants:
                variants.append(text)
        if not variants:
            raise ValueError("gold_answer must be non-empty")
        if len(variants) > 3:
            variants = variants[:3]
        self.gold_answer_variants = variants
        if self.gold_answer != variants[0]:
            self.gold_answer = variants[0]
        return self


class QuestionBundle(BaseModel):
    main_question: str
    gold_answer: str
    questions: list[ScoredQuestion] = Field(default_factory=list)
    supported_conclusions: list[str] = Field(default_factory=list)
    steps: list[DeductionStep] = Field(default_factory=list)
    counterfactual: CounterfactualTask | None = None
    falsifier: FalsifierTask | None = None

    @model_validator(mode="after")
    def _ensure_question_bundle(self) -> QuestionBundle:
        if not (2 <= len(self.questions) <= 4):
            raise ValueError("QuestionBundle must contain 2–4 scored questions")
        main = next(
            (q for q in self.questions if q.question_type == "main"),
            self.questions[0],
        )
        self.main_question = main.question
        self.gold_answer = main.gold_answer
        return self
