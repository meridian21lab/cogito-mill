"""Deterministic conditional-edge decisions for bounded graph repairs."""

from __future__ import annotations

from cogito_mill.pipelines.state import MillState


def route_concept(state: MillState) -> str:
    decision = state["concept_critic"].decision
    if decision == "accept":
        return "formalize"
    attempts = state.get("attempt_counts", {}).get("concept", 0)
    if decision == "revise" and attempts < 1 + state["recipe"].max_concept_repairs:
        return "plan_concept"
    return "reject_run"


def route_verification(state: MillState) -> str:
    return "tell_story" if not state.get("errors") else "reject_run"


def route_story(state: MillState) -> str:
    if state["story_critic"].decision == "accept":
        return "critique_final"
    attempts = state.get("attempt_counts", {}).get("story", 0)
    if attempts < 1 + state["recipe"].max_stage_repairs:
        return "tell_story"
    return "reject_run"


def route_final(state: MillState) -> str:
    if state["final_critic"].decision == "accept":
        return "final_validate"
    attempts = state.get("attempt_counts", {}).get("story", 0)
    if state["final_critic"].decision == "revise" and (
        attempts < 1 + state["recipe"].max_stage_repairs
    ):
        return "tell_story"
    return "reject_run"


__all__ = ["route_concept", "route_final", "route_story", "route_verification"]
