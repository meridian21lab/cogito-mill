"""Agent adapters and critic gates for the mill."""

from __future__ import annotations

from cogito_mill.agents.critics import critique_story_document, load_prompt

# Placeholder runtime identity retained for integration smoke tests.
def agent_runtime_name() -> str:
    return "deepagents+langgraph"


__all__ = [
    "agent_runtime_name",
    "critique_story_document",
    "load_prompt",
]
