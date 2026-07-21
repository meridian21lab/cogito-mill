"""Small, serializable deductive theory used by concept-induction stories."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class LogicAtom(BaseModel):
    """A ground predicate; arguments are stable entity or concept identifiers."""

    predicate: str
    arguments: list[str] = Field(default_factory=list)

    @property
    def key(self) -> str:
        return ":".join([self.predicate, *self.arguments])


class LogicRule(BaseModel):
    """A deterministic ground Horn rule."""

    id: str
    premises: list[LogicAtom]
    conclusion: LogicAtom
    explanation: str

    @model_validator(mode="after")
    def _has_premises(self) -> LogicRule:
        if not self.premises:
            raise ValueError("logic rule must have at least one premise")
        return self


class LogicTheory(BaseModel):
    """Visible facts and rules whose closure must identify exactly one candidate."""

    facts: list[LogicAtom]
    rules: list[LogicRule]
    goal_predicate: str = "qualifies"


__all__ = ["LogicAtom", "LogicRule", "LogicTheory"]
