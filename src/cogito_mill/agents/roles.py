"""Narrow model-backed agent roles for the explicit mill graph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from cogito_mill.domain.concept import ConceptBrief, CriticFinding, CriticReport
from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.narrative import StoryDocument, StoryDraft
from cogito_mill.domain.questions import QuestionBundle
from cogito_mill.domain.recipe import GenerationRecipe
from cogito_mill.llm.protocol import StructuredModel, build_structured_model


class AgentSuite(Protocol):
    def plan(
        self,
        recipe: GenerationRecipe,
        *,
        family_id: str,
        setting: str,
        concept: str,
        feedback: str = "",
    ) -> ConceptBrief: ...

    def critique_concept(
        self,
        recipe: GenerationRecipe,
        concept: ConceptBrief,
        *,
        family_id: str,
    ) -> CriticReport: ...

    def tell_story(
        self,
        concept: ConceptBrief,
        visible: VisibleTheory,
        scaffold: StoryDraft,
        *,
        feedback: str = "",
    ) -> StoryDraft: ...

    def critique_story(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
        *,
        grounding: CriticReport,
    ) -> CriticReport: ...

    def critique_final(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
    ) -> CriticReport: ...


@dataclass
class OfflineAgentSuite:
    """Deterministic adapters used by default tests and reproducible generation."""

    def plan(
        self,
        recipe: GenerationRecipe,
        *,
        family_id: str,
        setting: str,
        concept: str,
        feedback: str = "",
    ) -> ConceptBrief:
        return ConceptBrief(
            premise=f"A {family_id.replace('_', ' ')} mystery in {setting}.",
            setting_summary=setting,
            target_question=f"Who satisfies the locally defined concept {concept}?",
            intended_answer="selected only by the deterministic formal theory",
            composition_notes=(
                "Disperse times, places, travel constraints, and alibis across ordinary "
                "activity. Keep the opportunity rule explicit without arithmetic ledgers."
            ),
        )

    def critique_concept(
        self,
        recipe: GenerationRecipe,
        concept: ConceptBrief,
        *,
        family_id: str,
    ) -> CriticReport:
        return _accept("concept is formalizable and delegates truth to the solver")

    def tell_story(
        self,
        concept: ConceptBrief,
        visible: VisibleTheory,
        scaffold: StoryDraft,
        *,
        feedback: str = "",
    ) -> StoryDraft:
        return scaffold

    def critique_story(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
        *,
        grounding: CriticReport,
    ) -> CriticReport:
        return _accept("offline critic defers to deterministic story gates")

    def critique_final(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
    ) -> CriticReport:
        return _accept("offline final critic defers to deterministic validation")


class LiveAgentSuite:
    """Azure/GLM writer and judge adapters; routing remains deterministic."""

    def __init__(
        self,
        provider: str,
        *,
        writer: StructuredModel | None = None,
        judge: StructuredModel | None = None,
    ) -> None:
        self.writer = writer or build_structured_model(provider, "writer")
        self.judge = judge or build_structured_model(provider, "judge")

    def plan(
        self,
        recipe: GenerationRecipe,
        *,
        family_id: str,
        setting: str,
        concept: str,
        feedback: str = "",
    ) -> ConceptBrief:
        mechanism = (
            """The mystery is a connected custody-provenance puzzle. Every named person has
local access, so opportunity alone cannot answer it. A uniquely numbered authorization object
moves inside sealed containers through witnessed handoffs and uninspected whole-content
transfers. The answer requires following the shared object/container state from its opening
location to a final authorization record. Do not choose or hint at the answer; deterministic
code fixes the chain."""
            if recipe.prompt_version == "pilot.v5"
            else """The mystery is a timeline/opportunity puzzle: an incident happens in a fixed
time window at one place, and only one person could have been there for the whole window after
travel times and alibis are applied."""
        )
        prompt = f"""You are the concept planner for a synthetic reasoning benchmark.
Create one compact narrative premise for the fixed family {family_id!r}.
The setting must remain: {setting}
The target label must remain exactly: {concept}
{mechanism}
Do not invent arithmetic tallies, status scales, coefficients, or protocols. The formalizer and
deterministic code choose the answer. Prefer a natural day-in-the-life incident.
Prior critic feedback: {feedback or "none"}
Recipe: {recipe.model_dump_json()}
"""
        return self.writer.invoke_structured(ConceptBrief, prompt)

    def critique_concept(
        self,
        recipe: GenerationRecipe,
        concept: ConceptBrief,
        *,
        family_id: str,
    ) -> CriticReport:
        mechanism_gate = (
            "explicit need to compose sealed-container handoffs, whole-content transfers, and a final "
            "authorization record; every suspect has local opportunity"
            if recipe.prompt_version == "pilot.v5"
            else "explicit need to combine times, places, travel, and alibis"
        )
        prompt = f"""You are an independent concept critic. Return accept, revise, or reject.
Gate the proposal for: compatibility with family {family_id}; self-containment; a natural
narrative premise; no answer hint; {mechanism_gate}; and low resemblance to a stock locked-room
mystery. Reject premises that rely on status scales,
checksums, coefficient lists, or protocol ledgers. The success condition is: only one person
is derived by the disclosed formal mechanism. Recommend revision only when a listed gate fails.
Do not judge formal truth—the deterministic solver does that.
Recipe: {recipe.model_dump_json()}
Proposal: {concept.model_dump_json()}
"""
        return self.judge.invoke_structured(CriticReport, prompt)

    def tell_story(
        self,
        concept: ConceptBrief,
        visible: VisibleTheory,
        scaffold: StoryDraft,
        *,
        feedback: str = "",
    ) -> StoryDraft:
        obligations = {
            scene.id: [fact.text for fact in visible.facts if fact.id in scene.obligated_fact_ids]
            for scene in scaffold.scenes
        }
        spine_prompt = f"""You are the storyteller for a machine-verified deduction dataset.
Phase 1 — simple factual storyline only.
Write a title, opening, and the same five scene IDs as a clear account of the incident and every
obligated fact. No literary padding yet. Preserve people, objects, containers, custody handoffs,
whole-content transfers, places, and clock times exactly. A transfer moves unexamined contents;
never identify the authorization object during a transfer or state which container it enters.
Do not reveal the final custodian or culprit. State observations without explaining the full
deduction. Use only the people named in the obligations; do not invent additional named people.
Never write any participant's contiguous full name (given name immediately followed by surname).
Keep surnames in separate clauses, as in the obligations. Never use protocol declarations,
status scales, coefficients, modulo arithmetic, checksums, tallies, or six-stream ledgers.
Do not invent twin-name suffixes.
Concept: {concept.model_dump_json()}
Scene obligations: {json.dumps(obligations, ensure_ascii=False)}
Scaffold: {scaffold.model_dump_json()}
Repair feedback: {feedback or "none"}
"""
        spine = self.writer.invoke_structured(StoryDraft, spine_prompt)
        polish_prompt = f"""You are the storyteller for a machine-verified deduction dataset.
Phase 2 — add light noise, then regenerate into one coherent human-readable mystery.
You receive a fact-true spine. Preserve every named participant, object, container, custody
handoff, whole-content transfer, place, clock time, duration, and travel claim. Weave ordinary activity
(errands, food, work tasks, small talk) around the critical observations. Return a title,
opening, and the same five scene IDs.
Write like a short literary mystery or true-crime vignette, not a procedure manual.
A careful reader should be able to reconstruct the changing physical state.
Never write any participant's contiguous full name; keep surnames in separate clauses.
Never name or identify the authorization object while narrating a whole-content transfer; the
reader must propagate its opening location. State observations without narrating the answer or
labeling distractors as irrelevant. Use only people named in the obligations and do not invent
additional named people.
Never use protocol declarations, status scales, coefficients, modulo arithmetic, checksums,
tallies, or six-stream ledgers. Do not invent twin-name suffixes or personnel-index walls.
Do not state who finishes with the authorization object.
Concept: {concept.model_dump_json()}
Scene obligations: {json.dumps(obligations, ensure_ascii=False)}
Fact-true spine: {spine.model_dump_json()}
Scaffold obligation ids: {scaffold.model_dump_json()}
Repair feedback: {feedback or "none"}
"""
        return self.writer.invoke_structured(StoryDraft, polish_prompt)

    def critique_story(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
        *,
        grounding: CriticReport,
    ) -> CriticReport:
        prompt = f"""You are a blind narrative-quality critic for a reasoning benchmark.
Hard failures only (return revise/reject): explicit tables/bullet ledgers; personnel-index
walls; formulaic protocol/status/coefficient/checksum language; answer asserted in the story;
missing obligated custody/object/time facts; contradictory handoffs or timelines; unreadable
prose. The story must read as a human mystery with ordinary activity carrying the evidence.
Soft style issues alone are not grounds for revise when deterministic gates
pass. Return accept when the story is usable narration and questions are unambiguous.
Deterministic grounding has priority and reports:
{grounding.model_dump_json()}
Story: {story.full_text}
Questions: {questions.model_dump_json()}
"""
        return self.judge.invoke_structured(CriticReport, prompt)

    def critique_final(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
    ) -> CriticReport:
        prompt = f"""You are the final usability critic. The question bundle includes private
gold answers and variants for dataset validation; these fields are never shown to the solver
and are not answer leaks. Judge direct leakage only inside the story and reader-facing question
text. Deterministic code has already verified unique disclosure; do not recompute the
formal proof. Accept only if the item is self-contained, reads as a human story with a
followable evidence chain, does not use status-scale or checksum ledgers, does not state the
answer, and asks precise questions with explicit answer forms.
Revise if wording can fix it; reject if unusable.
Story: {story.full_text}
Questions: {questions.model_dump_json()}
"""
        return self.judge.invoke_structured(CriticReport, prompt)


def _accept(detail: str) -> CriticReport:
    return CriticReport(
        decision="accept",
        findings=[CriticFinding(gate="agent_review", passed=True, detail=detail)],
        feedback=detail,
    )


__all__ = ["AgentSuite", "LiveAgentSuite", "OfflineAgentSuite"]
