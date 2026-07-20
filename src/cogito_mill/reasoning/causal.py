"""Deterministic causal event simulator."""

from __future__ import annotations

from copy import deepcopy

from cogito_mill.domain.world import Event, WorldSpec


def _base_facts(world: WorldSpec) -> set[str]:
    facts = set(world.facts)
    for rel in world.relations:
        facts.add(f"rel:{rel.kind.value}:{rel.subject}:{rel.object}")
        if rel.kind.value == "has_access":
            facts.add(f"has_access_{rel.subject}_{rel.object}")
        if rel.kind.value == "owns":
            facts.add(f"{rel.subject}_owns_{rel.object}")
    return facts


def simulate(
    world: WorldSpec,
    *,
    disabled_events: set[str] | None = None,
) -> tuple[set[str], list[str]]:
    """Execute enabled events in time order; return facts and causal trace."""
    disabled = disabled_events or set()
    facts = _base_facts(world)
    by_time = sorted(
        [e for e in world.events if e.id not in disabled and e.enabled],
        key=lambda e: next(t.order for t in world.time_points if t.id == e.time_point),
    )
    trace: list[str] = []
    for event in by_time:
        if any(inh in facts for inh in event.inhibitors):
            continue
        if all(pre in facts for pre in event.preconditions):
            for effect in event.effects:
                facts.add(effect)
            trace.append(event.id)
    return facts, trace


def with_disabled_event(world: WorldSpec, event_id: str) -> WorldSpec:
    clone = deepcopy(world)
    for event in clone.events:
        if event.id == event_id:
            event.enabled = False
    return clone


def event_map(world: WorldSpec) -> dict[str, Event]:
    return {e.id: e for e in world.events}
