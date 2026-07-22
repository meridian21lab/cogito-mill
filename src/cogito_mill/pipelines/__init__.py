"""Pipeline package exports."""

from __future__ import annotations

from cogito_mill.pipelines.graph import build_mill_graph
from cogito_mill.pipelines.runner import generate_batch, generate_one


def pipeline_stages() -> tuple[str, ...]:
    return (
        "sample_recipe",
        "formalize_and_disclose",
        "critique_story",
        "final_validate",
        "pack",
        "publish",
        "evaluate",
    )


__all__ = [
    "build_mill_graph",
    "generate_batch",
    "generate_one",
    "pipeline_stages",
]
