"""Deterministic forward chaining for visible concept theories."""

from __future__ import annotations

from dataclasses import dataclass

from cogito_mill.domain.logic import LogicAtom, LogicRule, LogicTheory


@dataclass(frozen=True)
class Derivation:
    atom: LogicAtom
    rule_id: str | None
    premise_keys: tuple[str, ...] = ()


def derive(theory: LogicTheory) -> dict[str, Derivation]:
    """Return the least fixed-point closure and one proof parent set per atom."""
    closure = {atom.key: Derivation(atom=atom, rule_id=None) for atom in theory.facts}
    changed = True
    while changed:
        changed = False
        for rule in theory.rules:
            for bindings, premise_keys in _matching_bindings(rule, closure):
                conclusion = _instantiate(rule.conclusion, bindings)
                if conclusion.key not in closure:
                    closure[conclusion.key] = Derivation(
                        atom=conclusion,
                        rule_id=rule.id,
                        premise_keys=premise_keys,
                    )
                    changed = True
    return closure


def goal_candidates(theory: LogicTheory, candidates: list[str]) -> list[str]:
    closure = derive(theory)
    return [
        candidate
        for candidate in candidates
        if LogicAtom(predicate=theory.goal_predicate, arguments=[candidate]).key in closure
    ]


def proof_keys(theory: LogicTheory, goal: LogicAtom) -> list[str]:
    """Topologically collect atoms needed for one derived goal."""
    closure = derive(theory)
    ordered: list[str] = []
    seen: set[str] = set()

    def visit(key: str) -> None:
        if key in seen or key not in closure:
            return
        seen.add(key)
        for premise in closure[key].premise_keys:
            visit(premise)
        ordered.append(key)

    visit(goal.key)
    return ordered


def _matching_bindings(
    rule: LogicRule,
    closure: dict[str, Derivation],
) -> list[tuple[dict[str, str], tuple[str, ...]]]:
    candidates = [entry.atom for entry in closure.values()]
    partial: list[tuple[dict[str, str], tuple[str, ...]]] = [({}, ())]
    for premise in rule.premises:
        expanded: list[tuple[dict[str, str], tuple[str, ...]]] = []
        for bindings, keys in partial:
            for atom in candidates:
                matched = _unify(premise, atom, bindings)
                if matched is not None:
                    expanded.append((matched, (*keys, atom.key)))
        partial = expanded
        if not partial:
            break
    return partial


def _unify(
    pattern: LogicAtom,
    atom: LogicAtom,
    bindings: dict[str, str],
) -> dict[str, str] | None:
    if pattern.predicate != atom.predicate or len(pattern.arguments) != len(atom.arguments):
        return None
    result = dict(bindings)
    for expected, actual in zip(pattern.arguments, atom.arguments, strict=True):
        if expected.startswith("?"):
            bound = result.get(expected)
            if bound is not None and bound != actual:
                return None
            result[expected] = actual
        elif expected != actual:
            return None
    return result


def _instantiate(pattern: LogicAtom, bindings: dict[str, str]) -> LogicAtom:
    return LogicAtom(
        predicate=pattern.predicate,
        arguments=[bindings.get(arg, arg) for arg in pattern.arguments],
    )


__all__ = ["Derivation", "derive", "goal_candidates", "proof_keys"]
