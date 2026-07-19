"""Validators for story integrity, answerability, and schema conformance."""

from __future__ import annotations


def is_nonempty(text: str) -> bool:
    return bool(text and text.strip())
