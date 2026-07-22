"""Z3 compiler for relational narrative constraint worlds."""

from __future__ import annotations

from dataclasses import dataclass

import z3  # type: ignore[import-untyped]

from cogito_mill.domain.constraints import ConstraintClue, ConstraintTheory


@dataclass(frozen=True)
class ConstraintSolution:
    assignments: dict[str, dict[str, str]]


@dataclass
class _Compiled:
    solver: z3.Solver
    object_vars: list[z3.ArithRef]
    place_vars: list[z3.ArithRef]
    time_vars: list[z3.ArithRef]


def target_candidates(theory: ConstraintTheory) -> list[str]:
    """Return people who can own the target object in some satisfying world."""
    compiled = _compile(theory)
    target = theory.objects.index(theory.target_object)
    candidates: list[str] = []
    for index, person in enumerate(theory.people):
        compiled.solver.push()
        compiled.solver.add(compiled.object_vars[index] == target)
        if compiled.solver.check() == z3.sat:
            candidates.append(person)
        compiled.solver.pop()
    return candidates


def solve_unique(theory: ConstraintTheory) -> ConstraintSolution | None:
    """Return the complete assignment only when the visible world is unique."""
    compiled = _compile(theory)
    if compiled.solver.check() != z3.sat:
        return None
    model = compiled.solver.model()
    values = [
        *[model.eval(var).as_long() for var in compiled.object_vars],
        *[model.eval(var).as_long() for var in compiled.place_vars],
        *[model.eval(var).as_long() for var in compiled.time_vars],
    ]
    all_vars = [*compiled.object_vars, *compiled.place_vars, *compiled.time_vars]
    compiled.solver.add(z3.Or([var != value for var, value in zip(all_vars, values, strict=True)]))
    if compiled.solver.check() == z3.sat:
        return None
    n = len(theory.people)
    return ConstraintSolution(
        assignments={
            person: {
                "object": theory.objects[values[index]],
                "place": theory.places[values[n + index]],
                "time": theory.times[values[2 * n + index]],
            }
            for index, person in enumerate(theory.people)
        }
    )


def _compile(theory: ConstraintTheory) -> _Compiled:
    n = len(theory.people)
    if not (n == len(theory.objects) == len(theory.places) == len(theory.times)):
        raise ValueError("constraint axes must have equal cardinality")
    solver = z3.Solver()
    object_vars = [z3.Int(f"object_{index}") for index in range(n)]
    place_vars = [z3.Int(f"place_{index}") for index in range(n)]
    time_vars = [z3.Int(f"time_{index}") for index in range(n)]
    for variables in (object_vars, place_vars, time_vars):
        solver.add(z3.Distinct(variables))
        for variable in variables:
            solver.add(variable >= 0, variable < n)

    people = {value: index for index, value in enumerate(theory.people)}
    objects = {value: index for index, value in enumerate(theory.objects)}
    places = {value: index for index, value in enumerate(theory.places)}
    times = {value: index for index, value in enumerate(theory.times)}
    for clue in theory.clues:
        solver.add(
            _compile_clue(
                clue,
                people=people,
                objects=objects,
                places=places,
                times=times,
                object_vars=object_vars,
                place_vars=place_vars,
                time_vars=time_vars,
            )
        )
    return _Compiled(solver, object_vars, place_vars, time_vars)


def _compile_clue(
    clue: ConstraintClue,
    *,
    people: dict[str, int],
    objects: dict[str, int],
    places: dict[str, int],
    times: dict[str, int],
    object_vars: list[z3.ArithRef],
    place_vars: list[z3.ArithRef],
    time_vars: list[z3.ArithRef],
) -> z3.BoolRef:
    args = clue.arguments
    if clue.kind == "person_not_place":
        return place_vars[people[args[0]]] != places[args[1]]
    if clue.kind == "person_not_time":
        return time_vars[people[args[0]]] != times[args[1]]
    if clue.kind == "object_not_place":
        return z3.Not(
            _value_pair_exists(
                object_vars,
                objects[args[0]],
                place_vars,
                places[args[1]],
            )
        )
    if clue.kind == "object_not_time":
        return z3.Not(
            _value_pair_exists(
                object_vars,
                objects[args[0]],
                time_vars,
                times[args[1]],
            )
        )
    if clue.kind == "place_not_time":
        return z3.Not(
            _value_pair_exists(
                place_vars,
                places[args[0]],
                time_vars,
                times[args[1]],
            )
        )
    if clue.kind == "person_before_person":
        return time_vars[people[args[0]]] < time_vars[people[args[1]]]
    if clue.kind == "object_before_object":
        return _axis_time(object_vars, objects[args[0]], time_vars) < _axis_time(
            object_vars, objects[args[1]], time_vars
        )
    if clue.kind == "place_before_place":
        return _axis_time(place_vars, places[args[0]], time_vars) < _axis_time(
            place_vars, places[args[1]], time_vars
        )
    if clue.kind == "person_place_xor_time":
        person = people[args[0]]
        return z3.Xor(
            place_vars[person] == places[args[1]],
            time_vars[person] == times[args[2]],
        )
    if clue.kind == "object_place_xor_time":
        return z3.Xor(
            _value_pair_exists(
                object_vars,
                objects[args[0]],
                place_vars,
                places[args[1]],
            ),
            _value_pair_exists(
                object_vars,
                objects[args[0]],
                time_vars,
                times[args[2]],
            ),
        )
    raise ValueError(f"unsupported constraint kind: {clue.kind}")


def _value_pair_exists(
    left_vars: list[z3.ArithRef],
    left_value: int,
    right_vars: list[z3.ArithRef],
    right_value: int,
) -> z3.BoolRef:
    return z3.Or(
        [
            z3.And(left == left_value, right == right_value)
            for left, right in zip(left_vars, right_vars, strict=True)
        ]
    )


def _axis_time(
    axis_vars: list[z3.ArithRef],
    axis_value: int,
    time_vars: list[z3.ArithRef],
) -> z3.ArithRef:
    return z3.Sum(
        [
            z3.If(axis == axis_value, time, 0)
            for axis, time in zip(axis_vars, time_vars, strict=True)
        ]
    )


__all__ = ["ConstraintSolution", "solve_unique", "target_candidates"]
