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
                "Disperse six independent relational, temporal, causal, spatial, sequence, "
                "and protocol streams. Keep the checksum rule explicit and every candidate "
                "plausible."
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
        prompt = f"""You are the concept planner for a synthetic reasoning benchmark.
Create one compact narrative premise for the fixed family {family_id!r}.
The setting must remain: {setting}
The locally defined target concept must remain exactly: {concept}
Define that concept crisply as the one participant whose six evidence statuses produce the
incident's accepted iterated modular checksum under the local rules. The statuses are relational,
temporal, causal, spatial, sequence, and protocol evidence. Do not choose or hint at the
answer. The formalizer and deterministic code will choose
the answer. Make the premise natural, self-contained, and unlike a generic murder mystery.
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
        prompt = f"""You are an independent concept critic. Return accept, revise, or reject.
Gate the proposal for: compatibility with family {family_id}; self-containment; a natural
narrative premise; no answer hint; explicit need to combine relational, temporal, causal,
spatial, sequence, and local-protocol evidence; and low resemblance to a stock locked-room
mystery. The benchmark intentionally defines its target concept locally as the person whose
six-stream iterated modular checksum equals the accepted checksum. Treat that as a crisp success
condition; do not demand an external job title or add another condition. Recommend revision
only when a listed gate actually fails.
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
        prompt = f"""You are the storyteller for a machine-verified deduction dataset.
Write an engaging, coherent short mystery as a title, opening, and the same five scene IDs.
Use the supplied scaffold only as structural guidance; vary voice, pacing, transitions,
scene openings, and paragraph rhythm. Do not reveal which person satisfies the final concept.

CRITICAL GROUNDING CONTRACT:
- Realize every obligation faithfully in its assigned scene exactly once. Natural paraphrase is
  allowed, but preserve every named participant, value, relation, condition, and consequence.
- Combine related conversion facts into motivated prose where that improves narration. Explain
  why an auditor, witness, or participant checks each alternative instead of serializing a table.
- You may add connective narration, reactions, and atmosphere, but no new logical facts.
- Do not turn the evidence into a table, ledger dump, bullet list, or repeated template.
- Give the six evidence streams distinct incident functions and scene-level purposes.
- Keep all local rules explicit. A reader must be able to solve without outside knowledge.
- Each scene's obligated_fact_ids must remain exactly those in the scaffold.

Concept: {concept.model_dump_json()}
Scene obligations: {json.dumps(obligations, ensure_ascii=False)}
Scaffold: {scaffold.model_dump_json()}
Repair feedback: {feedback or "none"}
"""
        return self.writer.invoke_structured(StoryDraft, prompt)

    def critique_story(
        self,
        story: StoryDocument,
        questions: QuestionBundle,
        *,
        grounding: CriticReport,
    ) -> CriticReport:
        prompt = f"""You are a blind narrative-quality critic for a reasoning benchmark.
Return accept only if the story is coherent narration, each clue is naturally integrated,
the six evidence streams remain trackable but nontrivial, local rules are clear, prose is
not a disguised table, the answer is not asserted, and every question is unambiguous.
Return revise with actionable sentence-level feedback for repairable prose; reject only for
an irreparable premise. Deterministic grounding has priority and reports:
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
text. Deterministic code has already executed and verified the checksum; do not recompute or
override its arithmetic. Accept only if the item is self-contained, readable as a story,
materially requires combining dispersed evidence, does not state which candidate satisfies
the final concept in the story, and asks precise questions with explicit answer forms.
Revise if wording can fix it;
reject if unusable.
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
