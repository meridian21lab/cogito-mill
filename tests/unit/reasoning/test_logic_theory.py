"""Forward-chaining concept theory tests."""

from cogito_mill.domain.logic import LogicAtom, LogicRule, LogicTheory
from cogito_mill.pipelines.concept_templates import iterated_checksum
from cogito_mill.reasoning.logic import goal_candidates, proof_keys


def test_variable_rules_derive_one_candidate() -> None:
    theory = LogicTheory(
        facts=[
            LogicAtom(predicate="linked", arguments=["p1", "amber"]),
            LogicAtom(predicate="linked", arguments=["p2", "blue"]),
            LogicAtom(predicate="accepted", arguments=["amber"]),
            LogicAtom(predicate="active"),
        ],
        rules=[
            LogicRule(
                id="match",
                premises=[
                    LogicAtom(predicate="linked", arguments=["?person", "?value"]),
                    LogicAtom(predicate="accepted", arguments=["?value"]),
                ],
                conclusion=LogicAtom(predicate="marked", arguments=["?person"]),
                explanation="matching values receive a mark",
            ),
            LogicRule(
                id="qualify",
                premises=[
                    LogicAtom(predicate="marked", arguments=["?person"]),
                    LogicAtom(predicate="active"),
                ],
                conclusion=LogicAtom(predicate="qualifies", arguments=["?person"]),
                explanation="active marks qualify",
            ),
        ],
    )

    assert goal_candidates(theory, ["p1", "p2"]) == ["p1"]
    assert proof_keys(theory, LogicAtom(predicate="qualifies", arguments=["p1"])) == [
        "linked:p1:amber",
        "accepted:amber",
        "marked:p1",
        "active",
        "qualifies:p1",
    ]


def test_iterated_checksum_carries_state_across_all_five_cycles() -> None:
    result = iterated_checksum(
        (3, 5, 5, 2, 2, 1),
        (13, 7, 3, 11, 2, 5),
        start_value=12,
        modulus=97,
    )

    assert result == 19
