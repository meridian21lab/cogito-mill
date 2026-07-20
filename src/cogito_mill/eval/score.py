"""Answer normalization and exact scoring."""

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
