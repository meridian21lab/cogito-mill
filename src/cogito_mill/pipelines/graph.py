"""LangGraph assembly for the pilot mill."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from cogito_mill.agents.roles import AgentSuite, OfflineAgentSuite
from cogito_mill.pipelines.nodes import MillNodes
from cogito_mill.pipelines.routing import (
    route_concept,
    route_final,
    route_story,
    route_verification,
)
from cogito_mill.pipelines.state import MillState
from cogito_mill.reasoning import WorldSolver


def build_mill_graph(
    *,
    agents: AgentSuite | None = None,
    solver: WorldSolver | None = None,
) -> Any:
    """Compile the fixed, auditable agent graph with bounded repair loops."""
    nodes = MillNodes(
        agents=agents or OfflineAgentSuite(),
        solver=solver or WorldSolver(),
    )
    graph = StateGraph(MillState)
    graph.add_node("sample_recipe", nodes.sample_recipe)
    graph.add_node("plan_concept", nodes.plan_concept)
    graph.add_node("critique_concept", nodes.critique_concept)
    graph.add_node("formalize", nodes.formalize)
    graph.add_node("verify", nodes.verify)
    graph.add_node("tell_story", nodes.tell_story)
    graph.add_node("assemble_and_ground", nodes.assemble_and_ground)
    graph.add_node("critique_story", nodes.critique_story)
    graph.add_node("critique_final", nodes.critique_final)
    graph.add_node("final_validate", nodes.final_validate)
    graph.add_node("reject_run", nodes.reject_run)
    graph.add_edge(START, "sample_recipe")
    graph.add_edge("sample_recipe", "plan_concept")
    graph.add_edge("plan_concept", "critique_concept")
    graph.add_conditional_edges("critique_concept", route_concept)
    graph.add_edge("formalize", "verify")
    graph.add_conditional_edges("verify", route_verification)
    graph.add_edge("tell_story", "assemble_and_ground")
    graph.add_edge("assemble_and_ground", "critique_story")
    graph.add_conditional_edges("critique_story", route_story)
    graph.add_conditional_edges("critique_final", route_final)
    graph.add_edge("final_validate", END)
    graph.add_edge("reject_run", END)
    return graph.compile()


__all__ = ["build_mill_graph"]
