"""Formal hidden world model."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class RelationKind(StrEnum):
    WORKS_AT = "works_at"
    HAS_ACCESS = "has_access"
    LOCATED_IN = "located_in"
    OWNS = "owns"
    REPORTS_TO = "reports_to"
    PRESENT_AT = "present_at"
    CUSTOM = "custom"


class Entity(BaseModel):
    id: str
    type: str
    label: str
    attributes: dict[str, str] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)


class Relation(BaseModel):
    id: str
    kind: RelationKind
    subject: str
    object: str
    symmetric: bool = False
    exclusive_object: bool = False


class TimePoint(BaseModel):
    id: str
    label: str
    order: int


class Event(BaseModel):
    id: str
    label: str
    actor: str | None = None
    time_point: str
    preconditions: list[str] = Field(default_factory=list)
    effects: list[str] = Field(default_factory=list)
    inhibitors: list[str] = Field(default_factory=list)
    causal_parents: list[str] = Field(default_factory=list)
    enabled: bool = True


class Rule(BaseModel):
    id: str
    text: str
    formal: str


class TargetClaim(BaseModel):
    predicate: str
    arguments: list[str]
    expected_value: str


class Intervention(BaseModel):
    id: str
    description: str
    disable_event: str
    expected_target_value: str


class WorldSpec(BaseModel):
    id: str
    entities: list[Entity]
    relations: list[Relation]
    time_points: list[TimePoint]
    events: list[Event]
    rules: list[Rule] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    target: TargetClaim
    intervention: Intervention | None = None
    answer_entity: str
    candidate_answers: list[str]

    @model_validator(mode="after")
    def _check_refs(self) -> WorldSpec:
        entity_ids = {e.id for e in self.entities}
        time_ids = {t.id for t in self.time_points}
        event_ids = {e.id for e in self.events}
        if self.answer_entity not in entity_ids:
            raise ValueError(f"answer_entity {self.answer_entity!r} missing")
        for rel in self.relations:
            if rel.subject not in entity_ids or rel.object not in entity_ids:
                raise ValueError(f"relation {rel.id} references unknown entity")
        for event in self.events:
            if event.time_point not in time_ids:
                raise ValueError(f"event {event.id} unknown time_point")
            if event.actor and event.actor not in entity_ids:
                raise ValueError(f"event {event.id} unknown actor")
            for parent in event.causal_parents:
                if parent not in event_ids:
                    raise ValueError(f"event {event.id} unknown parent {parent}")
        if self.intervention and self.intervention.disable_event not in event_ids:
            raise ValueError("intervention.disable_event unknown")
        for cand in self.candidate_answers:
            if cand not in entity_ids:
                raise ValueError(f"candidate {cand!r} missing")
        return self
