"""Generation and evaluation pipelines."""

from __future__ import annotations


def pipeline_stages() -> tuple[str, ...]:
    return ("design", "generate", "verify", "package", "publish")
