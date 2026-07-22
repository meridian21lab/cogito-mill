"""Companion solver appendix for accepted items (not part of the thin Hub schema)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cogito_mill.domain.questions import FalsifierTask
from cogito_mill.domain.reasoning import DeductionStep


class TimelineSegment(BaseModel):
    place: str
    start_minute: int
    end_minute: int
    fact_id: str
    summary: str = ""


class EliminationNote(BaseModel):
    person_label: str
    reason: str
    fact_ids: list[str] = Field(default_factory=list)


class EvidenceIntervention(BaseModel):
    """Minimal evidence edit for a counterfactual question."""

    person_id: str
    person_label: str
    fact_id: str
    description: str
    answer_label: str
    secondary_person_id: str | None = None
    secondary_person_label: str | None = None
    secondary_fact_id: str | None = None
    secondary_description: str | None = None

    def question_clause(self) -> str:
        if self.secondary_description:
            return f"{self.secondary_description} and {self.description}"
        return self.description

    def fact_ids(self) -> list[str]:
        ids = [self.fact_id]
        if self.secondary_fact_id:
            ids.append(self.secondary_fact_id)
        return ids


class ProvenanceState(BaseModel):
    """One auditable state in a custody-provenance chain."""

    step: int
    token_container: str
    carriers: dict[str, str] = Field(default_factory=dict)
    event_fact_id: str | None = None
    summary: str = ""


class SolverAppendix(BaseModel):
    """Proof-carrying sidecar for external solvers and human audit."""

    id: str
    schema_version: str = "appendix.v2"
    mechanism: str = "timeline_opportunity"
    incident: dict[str, Any] = Field(default_factory=dict)
    travel_minutes: dict[str, dict[str, int]] = Field(default_factory=dict)
    timelines: dict[str, list[TimelineSegment]] = Field(default_factory=dict)
    opportunity: dict[str, bool] = Field(default_factory=dict)
    eliminations: list[EliminationNote] = Field(default_factory=list)
    provenance_states: list[ProvenanceState] = Field(default_factory=list)
    gold_steps: list[DeductionStep] = Field(default_factory=list)
    supported_conclusions: list[str] = Field(default_factory=list)
    evidence_counterfactual: EvidenceIntervention | None = None
    falsifier: FalsifierTask | None = None
    notes: list[str] = Field(default_factory=list)

    def to_solver_text(self) -> str:
        """Render a compact logical flow for appendix-assisted evaluation."""
        lines = [
            "SOLVER APPENDIX (not part of the reader-facing story)",
            "Use this only as an explicit logical flow over story-grounded evidence.",
            f"Mechanism: {self.mechanism}",
            "",
        ]
        if self.incident:
            lines.append("Incident:")
            for key, value in self.incident.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
        if self.travel_minutes:
            lines.append("Travel times (minutes):")
            for origin, destinations in self.travel_minutes.items():
                for dest, minutes in destinations.items():
                    if origin < dest:
                        lines.append(f"- {origin} ↔ {dest}: {minutes}")
            lines.append("")
        if self.timelines:
            lines.append("Timelines (minute-of-day):")
            for person, segments in self.timelines.items():
                lines.append(f"- {person}:")
                for segment in segments:
                    lines.append(
                        f"  - {segment.start_minute}-{segment.end_minute} at "
                        f"{segment.place} [{segment.fact_id}] {segment.summary}"
                    )
            lines.append("")
        if self.opportunity:
            lines.append("Opportunity:")
            for person, has_opp in self.opportunity.items():
                lines.append(f"- {person}: {'yes' if has_opp else 'no'}")
            lines.append("")
        if self.eliminations:
            lines.append("Eliminations:")
            for note in self.eliminations:
                evidence = ", ".join(note.fact_ids) or "timeline"
                lines.append(f"- {note.person_label}: {note.reason} [{evidence}]")
            lines.append("")
        if self.provenance_states:
            lines.append("Custody provenance:")
            for state in self.provenance_states:
                evidence = f" [{state.event_fact_id}]" if state.event_fact_id else ""
                carriers = "; ".join(
                    f"{container} → {person}" for container, person in state.carriers.items()
                )
                lines.append(
                    f"- step {state.step}: token in {state.token_container}; {carriers}{evidence}"
                )
            lines.append("")
        if self.gold_steps:
            lines.append("Gold deduction steps:")
            for step in self.gold_steps:
                evidence = ", ".join(step.evidence_fact_ids) or "prior"
                lines.append(
                    f"- {step.id} ({step.inference_type}): {step.conclusion} [evidence: {evidence}]"
                )
            lines.append("")
        if self.evidence_counterfactual is not None:
            edit = self.evidence_counterfactual
            lines.extend(
                [
                    "Evidence-edit counterfactual:",
                    f"- {edit.question_clause()}",
                    f"- Cited facts: {', '.join(edit.fact_ids())}",
                    f"- Resulting answer: {edit.answer_label}",
                    "",
                ]
            )
        if self.falsifier is not None:
            lines.extend(
                [
                    f"Falsifier hypothesis: {self.falsifier.hypothesis}",
                    "Minimal contradicting evidence: " + ", ".join(self.falsifier.minimal_evidence),
                    "",
                ]
            )
        if self.supported_conclusions:
            lines.append("Supported conclusions:")
            for conclusion in self.supported_conclusions:
                lines.append(f"- {conclusion}")
        return "\n".join(lines).rstrip() + "\n"

    def model_dump_jsonl(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
