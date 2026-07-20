"""Scoring unit tests."""

from __future__ import annotations

from cogito_mill.eval.score import normalize_answer, score_exact


def test_normalize_and_exact() -> None:
    assert score_exact("Alice Chen", "alice chen")
    assert score_exact("FINAL name.", "final name")
    assert normalize_answer("  Foo  Bar ") == "foo bar"
    assert not score_exact("Alice", "Bob")
