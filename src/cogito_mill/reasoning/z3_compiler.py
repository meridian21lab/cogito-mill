"""Z3-backed candidate elimination over visible constraints."""

from __future__ import annotations

import z3  # type: ignore[import-untyped]

from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning.constraints import target_candidates
from cogito_mill.reasoning.logic import goal_candidates


def eliminate_candidates(
    world: WorldSpec,
    visible: VisibleTheory,
) -> list[str]:
    """Return candidates not ruled out by visible formal constraints.

    Supported formal atoms (pilot):
    - ``eliminated:<entity_id>``
    - ``requires_access:<place_id>`` combined with ``has_access:<entity>:<place>``
    - ``requires_item:<item_id>`` combined with ``holds:<entity>:<item>``
    - ``actor_must_be:<entity_id>``
    - ``present:<entity>:<place>`` / ``absent:<entity>:<place>``
    """
    if visible.constraints is not None:
        return target_candidates(visible.constraints)
    if visible.logic is not None:
        return goal_candidates(visible.logic, world.candidate_answers)

    atoms = {f.formal for f in visible.facts if f.formal}
    surviving: list[str] = []
    for cand in world.candidate_answers:
        if _candidate_survives(world, atoms, cand):
            surviving.append(cand)
    return surviving


def _candidate_survives(world: WorldSpec, atoms: set[str], cand: str) -> bool:
    if f"eliminated:{cand}" in atoms:
        return False
    if any(a.startswith("actor_must_be:") and a != f"actor_must_be:{cand}" for a in atoms):
        return False
    if f"actor_must_be:{cand}" in atoms:
        return True

    s = z3.Solver()
    alive = z3.Bool(f"alive_{cand}")
    s.add(alive)

    # Access requirements
    for atom in atoms:
        if atom.startswith("requires_access:"):
            place = atom.split(":", 1)[1]
            has = f"has_access:{cand}:{place}" in atoms or any(
                r.kind.value == "has_access" and r.subject == cand and r.object == place
                for r in world.relations
            )
            # also allow visible rel encoding
            has = has or f"rel:has_access:{cand}:{place}" in atoms
            if not has:
                s.add(z3.Not(alive))

        if atom.startswith("requires_item:"):
            item = atom.split(":", 1)[1]
            holds = f"holds:{cand}:{item}" in atoms
            if not holds:
                s.add(z3.Not(alive))

        if atom.startswith("absent:") and atom == f"absent:{cand}:{atom.split(':', 2)[-1]}":
            # handled below
            pass

    for atom in atoms:
        parts = atom.split(":")
        if len(parts) == 3 and parts[0] == "absent" and parts[1] == cand:
            s.add(z3.Not(alive))
        if len(parts) == 3 and parts[0] == "not_holds" and parts[1] == cand:
            s.add(z3.Not(alive))

    return bool(s.check() == z3.sat)


def assert_unique(surviving: list[str]) -> tuple[bool, str | None]:
    if len(surviving) == 1:
        return True, surviving[0]
    return False, None
