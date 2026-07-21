"""LangGraph assembly for the pilot mill."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from cogito_mill.pipelines.nodes import (
    critique_story,
    final_validate,
    formalize_and_disclose,
    sample_recipe,
)
from cogito_mill.pipelines.state import MillState


def build_mill_graph():
    """Explicit StateGraph: recipe → formalize → blind critic → final gate."""
    graph = StateGraph(MillState)
    graph.add_node("sample_recipe", sample_recipe)
    graph.add_node("formalize_and_disclose", formalize_and_disclose)
    graph.add_node("critique_story", critique_story)
    graph.add_node("final_validate", final_validate)
    graph.add_edge(START, "sample_recipe")
    graph.add_edge("sample_recipe", "formalize_and_disclose")
    graph.add_edge("formalize_and_disclose", "critique_story")
    graph.add_edge("critique_story", "final_validate")
    graph.add_edge("final_validate", END)
    return graph.compile()


__all__ = ["build_mill_graph"]
