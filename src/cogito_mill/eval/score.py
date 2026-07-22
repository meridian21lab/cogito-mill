"""Answer normalization and exact scoring (with optional variants)."""

from __future__ import annotations

import re
import unicodedata


def normalize_answer(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.strip().lower()
    text = re.sub(r"[\"'`]", "", text)
    text = re.sub(r"\s+", " ", text)
    # strip trailing punctuation
    text = text.rstrip(" .,:;!")
    return text


def score_exact(prediction: str, gold: str) -> bool:
    return normalize_answer(prediction) == normalize_answer(gold)


def score_exact_any(prediction: str, golds: list[str] | tuple[str, ...] | str) -> bool:
    """True if prediction matches any accepted gold string after normalization."""
    if isinstance(golds, str):
        candidates = [golds]
    else:
        candidates = list(golds)
    pred = normalize_answer(prediction)
    return any(pred == normalize_answer(g) for g in candidates if g)


def name_answer_variants(full_name: str) -> list[str]:
    """Build 1–3 legitimate full-name answer forms (never first-name-only)."""
    name = (full_name or "").strip()
    if not name:
        return []
    parts = name.split()
    variants = [name]
    if len(parts) >= 2:
        variants.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
    # Title-case already; keep a compacted single-space form if needed.
    compact = " ".join(parts)
    if compact not in variants:
        variants.append(compact)
    # Deduplicate, cap at 3, never admit a bare given name.
    out: list[str] = []
    for item in variants:
        if item not in out:
            out.append(item)
        if len(out) == 3:
            break
    return out
