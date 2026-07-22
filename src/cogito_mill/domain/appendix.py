"""Companion solver appendix for accepted items (not part of the thin Hub schema)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cogito_mill.domain.questions import FalsifierTask
from cogito_mill.domain.reasoning import DeductionStep


class StatusCell(BaseModel):
    status: str
    fact_id: str
    stream: str
    noun: str


class ChecksumParams(BaseModel):
    start_value: int
    coefficients: list[int]
    modulus: int
    cycle_count: int
    branch_order: list[str]
    pass_order: list[str] = Field(
        default_factory=lambda: [
            "forward",
            "reverse_with_reversed_coefficients",
            "forward_with_coefficients_rotated_left",
        ]
    )


class ChecksumCheckpoint(BaseModel):
    after_cycles: int
    person_id: str
    person_label: str
    value: int


class EvidenceIntervention(BaseModel):
    person_id: str
    person_label: str
    branch: str
    noun: str
    fact_id: str
    from_status: str
    to_status: str
    answer_label: str
    secondary_person_id: str | None = None
    secondary_person_label: str | None = None
    secondary_branch: str | None = None
    secondary_noun: str | None = None
    secondary_fact_id: str | None = None
    secondary_from_status: str | None = None
    secondary_to_status: str | None = None

    def question_clause(self) -> str:
        primary = (
            f"{self.person_label}'s {self.noun} status had been {self.to_status} "
            f"instead of {self.from_status}"
        )
        if (
            self.secondary_person_label
            and self.secondary_noun
            and self.secondary_to_status
            and self.secondary_from_status
        ):
            secondary = (
                f"{self.secondary_person_label}'s {self.secondary_noun} status had been "
                f"{self.secondary_to_status} instead of {self.secondary_from_status}"
            )
            return f"{secondary} and {primary}"
        return primary

    def fact_ids(self) -> list[str]:
        ids = [self.fact_id]
        if self.secondary_fact_id:
            ids.append(self.secondary_fact_id)
        return ids



class SolverAppendix(BaseModel):
    """Proof-carrying sidecar for external solvers and human audit."""

    id: str
    schema_version: str = "appendix.v1"
    status_matrix: dict[str, dict[str, StatusCell]] = Field(default_factory=dict)
    weights: dict[str, int] = Field(default_factory=dict)
    checksum_params: ChecksumParams
    candidate_checksums: dict[str, int] = Field(default_factory=dict)
    checkpoints: list[ChecksumCheckpoint] = Field(default_factory=list)
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
            "",
            "Status weights:",
        ]
        for status, weight in sorted(self.weights.items(), key=lambda item: item[1]):
            lines.append(f"- {status} = {weight}")
        params = self.checksum_params
        lines.extend(
            [
                "",
                "Checksum parameters:",
                f"- start_value = {params.start_value}",
                f"- branch_order = {', '.join(params.branch_order)}",
                f"- coefficients = {', '.join(str(c) for c in params.coefficients)}",
                f"- modulus = {params.modulus}",
                f"- cycle_count = {params.cycle_count}",
                f"- passes = {', '.join(params.pass_order)}",
                "",
                "Per-person status matrix (fact ids cite story obligations):",
            ]
        )
        for person, cells in self.status_matrix.items():
            cell_bits = [
                f"{branch}={cell.status}[{cell.fact_id}]" for branch, cell in cells.items()
            ]
            lines.append(f"- {person}: " + "; ".join(cell_bits))
        lines.extend(["", "Candidate checksums:"])
        for person, value in self.candidate_checksums.items():
            lines.append(f"- {person}: {value}")
        if self.checkpoints:
            lines.extend(["", "Checksum checkpoints (selected people):"])
            for point in self.checkpoints:
                lines.append(
                    f"- after {point.after_cycles} cycles, {point.person_label} = {point.value}"
                )
        if self.gold_steps:
            lines.extend(["", "Gold deduction steps:"])
            for step in self.gold_steps:
                evidence = ", ".join(step.evidence_fact_ids) or "prior"
                lines.append(
                    f"- {step.id} ({step.inference_type}): {step.conclusion} "
                    f"[evidence: {evidence}]"
                )
        if self.evidence_counterfactual is not None:
            edit = self.evidence_counterfactual
            lines.extend(
                [
                    "",
                    "Evidence-edit counterfactual:",
                    f"- {edit.question_clause()}",
                    f"- Cited facts: {', '.join(edit.fact_ids())}",
                    f"- Resulting answer: {edit.answer_label}",
                ]
            )
        if self.falsifier is not None:
            lines.extend(
                [
                    "",
                    f"Falsifier hypothesis: {self.falsifier.hypothesis}",
                    "Minimal contradicting evidence: "
                    + ", ".join(self.falsifier.minimal_evidence),
                ]
            )
        if self.supported_conclusions:
            lines.extend(["", "Supported conclusions:"])
            for conclusion in self.supported_conclusions:
                lines.append(f"- {conclusion}")
        return "\n".join(lines)

    def model_dump_jsonl(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
