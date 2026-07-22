"""Concept planning artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ConceptBrief(BaseModel):
    premise: str
    setting_summary: str
    target_question: str
    intended_answer: str
    composition_notes: str = ""
    version: int = 1


class CriticFinding(BaseModel):
    gate: str
    passed: bool
    detail: str


class CriticReport(BaseModel):
    decision: Literal["accept", "revise", "reject"]
    findings: list[CriticFinding] = Field(default_factory=list)
    feedback: str = ""
