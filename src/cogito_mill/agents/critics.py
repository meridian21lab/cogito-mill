"""Blind story critic — agents propose; deterministic gates decide."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Literal

from cogito_mill.domain.concept import CriticFinding, CriticReport
from cogito_mill.domain.narrative import StoryDocument
from cogito_mill.domain.questions import QuestionBundle

_EMP_RE = re.compile(r"\bEMP-\d+\b", re.IGNORECASE)
_PERSONNEL_INDEX_RE = re.compile(r"Personnel index:", re.IGNORECASE)
_PROMPTS = Path(__file__).resolve().parent / "prompts"

# Formulaic arithmetic / ledger patterns that must not dominate stories.
FORMULAIC_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"protocol active",
        r"status scale",
        r"counted as \d",
        r"coefficients?\s+\d",
        r"modulo\s+\d",
        r"six-stream",
        r"three-pass",
        r"squared the current",
        r"tally began at",
        r"local tally",
        r"checksum",
        r"relation, temporal, causal, spatial, sequence, and protocol",
        r"shared status scale",
        r"stream(?:'s|s)? coefficient",
        r"remainder modulo",
        r"both initialed the same custody line",
        r"with both seams in view",
    )
)

_AUTHORIZATION_TOKENS = (
    "numbered jeweler's release seal",
    "bronze archive seal",
    "ceramic command wafer",
    "numbered gallery release key",
    "brass relay cipher",
    "engraved treatment-room seal",
)
_DIRECT_TOKEN_TRANSFER_RE = re.compile(
    r"(?:moved|transferred|placed)\s+the\s+("
    + "|".join(re.escape(token) for token in _AUTHORIZATION_TOKENS)
    + r")\s+from\s+the\s+[^.!?]{1,100}\s+into\s+the\s+",
    re.IGNORECASE,
)

# Clock times, day-parts, and order words a reader can use for a timeline map.
TEMPORAL_MARKER_RE = re.compile(
    r"(?:"
    r"\b(?:a\.?m\.?|p\.?m\.?|o'clock|minutes?|hours?|before|after|until|"
    r"morning|midmorning|afternoon|evening|noon|midnight|half.?hour)\b"
    r"|\b(?:by|around|at|after|before)\s+\d{1,2}(?::\d{2})?\b"
    r"|\b\d{1,2}:\d{2}\b"
    r")",
    re.IGNORECASE,
)


def count_temporal_markers(text: str) -> int:
    return len(TEMPORAL_MARKER_RE.findall(text))


def load_prompt(name: str) -> str:
    path = _PROMPTS / name
    return path.read_text(encoding="utf-8")


def formulaic_hits(text: str) -> list[str]:
    return [pattern.pattern for pattern in FORMULAIC_PATTERNS if pattern.search(text)]


def direct_token_transfer_hits(text: str) -> list[str]:
    """Return token names whose transfer sentence resets the provenance chain."""
    return [match.group(1) for match in _DIRECT_TOKEN_TRANSFER_RE.finditer(text)]


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
            detail=(f"Personnel index lines={personnel_count} (max {max_personnel_index_lines})"),
        )
    )
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

    hits = formulaic_hits(text)
    findings.append(
        CriticFinding(
            gate="no_formulaic_ledger",
            passed=not hits,
            detail=(
                "no formulaic protocol/status/coefficient ledger"
                if not hits
                else f"formulaic ledger patterns: {', '.join(hits[:4])}"
            ),
        )
    )

    transfer_resets = direct_token_transfer_hits(text)
    findings.append(
        CriticFinding(
            gate="no_direct_token_transfer_reset",
            passed=not transfer_resets,
            detail=(
                "whole-content transfers do not directly reveal the tracked token"
                if not transfer_resets
                else f"direct token-transfer resets: {', '.join(transfer_resets[:3])}"
            ),
        )
    )

    temporal_markers = count_temporal_markers(text)
    findings.append(
        CriticFinding(
            gate="temporal_grounding",
            passed=temporal_markers >= 4,
            detail=f"temporal markers={temporal_markers} (min 4)",
        )
    )

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    sentence_lengths = [len(re.findall(r"\b[\w'-]+\b", sentence)) for sentence in sentences]
    if sentence_lengths:
        ordered = sorted(sentence_lengths)
        index = max(0, math.ceil(0.95 * len(ordered)) - 1)
        p95 = ordered[index]
    else:
        p95 = 0
    findings.append(
        CriticFinding(
            gate="sentence_length_p95",
            passed=p95 <= 45,
            detail=f"sentence_p95_words={p95} (max 45)",
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

    # Person-identity answers only: place/time intermediates may be multi-word without
    # "full name" in the stem.
    name_qs = [
        q
        for q in questions.questions
        if q.gold_answer.lower() != "none"
        and " " in q.gold_answer.strip()
        and (
            q.question_type in {"main", "counterfactual"}
            or (q.question_type == "intermediate" and "full name" in q.question.lower())
        )
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

    # Contiguous gold full names must not appear in reader-facing prose.
    leak_answers = [
        q.gold_answer
        for q in questions.questions
        if q.question_type in {"main", "counterfactual"}
        and q.gold_answer.lower() != "none"
        and " " in q.gold_answer.strip()
    ]
    if questions.gold_answer.lower() != "none":
        leak_answers.append(questions.gold_answer)
    leaked = []
    for answer in dict.fromkeys(leak_answers):
        pattern = rf"(?<![\w-]){re.escape(answer)}(?!-\d)(?![\w-])"
        if re.search(pattern, text):
            leaked.append(answer)
    findings.append(
        CriticFinding(
            gate="no_answer_leak",
            passed=not leaked,
            detail=(
                "no contiguous gold full name in story"
                if not leaked
                else f"story leaks gold name(s): {', '.join(leaked[:3])}"
            ),
        )
    )

    # Scalar / clock questions need an explicit answer form.
    scalar_qs = [q for q in questions.questions if q.question_type in {"scalar", "code"}]
    scalar_ok = all(
        "answer" in q.question.lower()
        and (
            "format" in q.question.lower()
            or "exact" in q.question.lower()
            or "only" in q.question.lower()
        )
        for q in scalar_qs
    )
    findings.append(
        CriticFinding(
            gate="scalar_answer_form",
            passed=scalar_ok,
            detail="scalar/code questions must state an explicit answer form",
        )
    )

    first = paragraphs[0] if paragraphs else ""
    opening_ok = bool(first) and ("Personnel index:" not in first and first.count("EMP-") < 3)
    findings.append(
        CriticFinding(
            gate="human_readable_opening",
            passed=opening_ok,
            detail="opening paragraph must read as narration, not an ID table",
        )
    )

    failed = [f for f in findings if not f.passed]
    decision: Literal["accept", "revise", "reject"]
    if failed:
        decision = "reject"
        feedback = "; ".join(f"{f.gate}: {f.detail}" for f in failed)
    else:
        decision = "accept"
        feedback = "story passes readability and QA contract gates"
    return CriticReport(decision=decision, findings=findings, feedback=feedback)
