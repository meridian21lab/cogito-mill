"""Scoring unit tests."""

from __future__ import annotations

from cogito_mill.eval.score import (
    name_answer_variants,
    normalize_answer,
    score_exact,
    score_exact_any,
)


def test_normalize_and_exact() -> None:
    assert score_exact("Alice Chen", "alice chen")
    assert score_exact("FINAL name.", "final name")
    assert normalize_answer("  Foo  Bar ") == "foo bar"
    assert not score_exact("Alice", "Bob")


def test_score_exact_any_variants() -> None:
    golds = name_answer_variants("Morgan Okada")
    assert "Morgan Okada" in golds
    assert "Okada, Morgan" in golds
    assert score_exact_any("morgan okada", golds)
    assert score_exact_any("Okada, Morgan", golds)
    assert not score_exact_any("Morgan", golds)


def test_name_variants_cap() -> None:
    variants = name_answer_variants("Avery Rossi")
    assert 1 <= len(variants) <= 3
    assert all(" " in v or "," in v for v in variants)
