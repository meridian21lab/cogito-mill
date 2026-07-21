"""Deterministic story assembly and exact visible-fact grounding."""

from __future__ import annotations

import re

from cogito_mill.domain.concept import CriticFinding, CriticReport
from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.narrative import Sentence, StoryDocument, StoryDraft


def assemble_story(
    draft: StoryDraft,
    visible: VisibleTheory,
    *,
    story_id: str,
) -> StoryDocument:
    paragraphs = [draft.opening.strip(), *(scene.prose.strip() for scene in draft.scenes)]
    full_text = "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
    sentences = [
        Sentence(id=f"sent-{idx}", text=text)
        for idx, text in enumerate(_sentences(full_text), start=1)
    ]
    mapping: dict[str, list[str]] = {}
    for fact in visible.facts:
        mapping[fact.id] = [
            sentence.id
            for sentence in sentences
            if fact.text.casefold() in sentence.text.casefold()
        ]
    return StoryDocument(
        id=story_id,
        title=draft.title,
        scenes=draft.scenes,
        sentences=sentences,
        full_text=full_text,
        fact_sentence_map=mapping,
    )


def critique_grounding(
    story: StoryDocument,
    visible: VisibleTheory,
) -> CriticReport:
    required = [fact for fact in visible.facts if fact.role == "required"]
    missing = [fact.id for fact in required if not story.fact_sentence_map.get(fact.id)]
    duplicated = [fact.id for fact in required if len(story.fact_sentence_map.get(fact.id, [])) > 1]
    known = {fact.id for fact in visible.facts}
    unknown_obligations = sorted(
        {
            fact_id
            for scene in story.scenes
            for fact_id in scene.obligated_fact_ids
            if fact_id not in known
        }
    )
    findings = [
        CriticFinding(
            gate="required_fact_grounding",
            passed=not missing,
            detail=f"missing required fact realizations: {missing}",
        ),
        CriticFinding(
            gate="single_fact_realization",
            passed=not duplicated,
            detail=f"facts repeated verbatim: {duplicated}",
        ),
        CriticFinding(
            gate="known_scene_obligations",
            passed=not unknown_obligations,
            detail=f"unknown scene obligations: {unknown_obligations}",
        ),
    ]
    failed = [finding for finding in findings if not finding.passed]
    return CriticReport(
        decision="revise" if failed else "accept",
        findings=findings,
        feedback=(
            "; ".join(f"{finding.gate}: {finding.detail}" for finding in failed)
            if failed
            else "all required visible facts are grounded exactly once"
        ),
    )


def _sentences(text: str) -> list[str]:
    return [
        match.group(0).strip()
        for match in re.finditer(r"[^.!?]+(?:[.!?]+|$)", text)
        if match.group(0).strip()
    ]


__all__ = ["assemble_story", "critique_grounding"]
