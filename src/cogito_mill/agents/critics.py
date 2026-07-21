"""Blind story critic — agents propose; deterministic gates decide."""

from __future__ import annotations

import re
from pathlib import Path

from cogito_mill.domain.concept import CriticFinding, CriticReport
from cogito_mill.domain.narrative import StoryDocument
from cogito_mill.domain.questions import QuestionBundle

_EMP_RE = re.compile(r"\bEMP-\d+\b", re.IGNORECASE)
_PERSONNEL_INDEX_RE = re.compile(r"Personnel index:", re.IGNORECASE)
_PROMPTS = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    path = _PROMPTS / name
    return path.read_text(encoding="utf-8")


def critique_story_document(
    story: StoryDocument,
    questions: QuestionBundle,
    *,
    max_emp_tokens: int = 14,
    max_personnel_index_lines: int = 2,
    min_paragraphs: int = 4,
) -> CriticReport:
    """Deterministic readability + QA-contract critic for pilot stories."""
    findings: list[CriticFinding] = []
    text = story.full_text or ""
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    emp_count = len(_EMP_RE.findall(text))
    personnel_count = len(_PERSONNEL_INDEX_RE.findall(text))

    findings.append(
        CriticFinding(
            gate="narrative_paragraphs",
            passed=len(paragraphs) >= min_paragraphs,
            detail=f"paragraphs={len(paragraphs)} (min {min_paragraphs})",
        )
    )
    findings.append(
        CriticFinding(
            gate="identifier_budget",
            passed=emp_count <= max_emp_tokens,
            detail=f"EMP tokens={emp_count} (max {max_emp_tokens})",
        )
    )
    findings.append(
        CriticFinding(
            gate="no_personnel_dump",
            passed=personnel_count <= max_personnel_index_lines,
            detail=(
                f"Personnel index lines={personnel_count} "
                f"(max {max_personnel_index_lines})"
            ),
        )
    )
    # Reject walls of nearly identical EMP mapping sentences.
    emp_lines = sum(
        1
        for line in re.split(r"[.\n]", text)
        if "resolves to" in line.lower() and _EMP_RE.search(line)
    )
    findings.append(
        CriticFinding(
            gate="no_id_resolution_wall",
            passed=emp_lines <= 3,
            detail=f"code→name resolution clauses={emp_lines} (max 3)",
        )
    )

    q_count = len(questions.questions)
    findings.append(
        CriticFinding(
            gate="question_count",
            passed=2 <= q_count <= 4,
            detail=f"scored questions={q_count} (need 2–4)",
        )
    )

    name_qs = [
        q
        for q in questions.questions
        if q.question_type in {"main", "intermediate", "counterfactual"}
        and q.gold_answer.lower() != "none"
    ]
    clear_form = all("full name" in q.question.lower() for q in name_qs)
    findings.append(
        CriticFinding(
            gate="answer_form_clarity",
            passed=clear_form,
            detail="name questions must request the full name explicitly",
        )
    )

    variant_ok = all(1 <= len(q.gold_answer_variants) <= 3 for q in questions.questions)
    findings.append(
        CriticFinding(
            gate="answer_variants",
            passed=variant_ok,
            detail="each question needs 1–3 gold_answer_variants",
        )
    )

    # Opening must read as narration, not an ID table.
    first = paragraphs[0] if paragraphs else ""
    opening_ok = bool(first) and (
        "Personnel index:" not in first and first.count("EMP-") < 3
    )
    findings.append(
        CriticFinding(
            gate="human_readable_opening",
            passed=opening_ok,
            detail="opening paragraph must read as narration, not an ID table",
        )
    )

    failed = [f for f in findings if not f.passed]
    if failed:
        decision = "reject"
        feedback = "; ".join(f"{f.gate}: {f.detail}" for f in failed)
    else:
        decision = "accept"
        feedback = "story passes readability and QA contract gates"
    return CriticReport(decision=decision, findings=findings, feedback=feedback)
