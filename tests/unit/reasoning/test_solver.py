"""Visible theory fixture aligned with office_badge world."""

from __future__ import annotations

import json
from pathlib import Path

from cogito_mill.domain.evidence import ClueChannel, VisibleFact, VisibleTheory
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning import WorldSolver

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "worlds" / "office_badge.json"


def load_world() -> WorldSpec:
    return WorldSpec.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def make_unique_visible(world: WorldSpec) -> VisibleTheory:
    return VisibleTheory(
        id="vis-office-1",
        world_id=world.id,
        facts=[
            VisibleFact(
                id="f1",
                text="Only someone with server-room access can perform the reboot.",
                formal="requires_access:server_room",
                channel=ClueChannel.RULE_APPLICATION,
                role="required",
                scene_id="sc1",
                reveal_order=1,
            ),
            VisibleFact(
                id="f2",
                text="Alice has server-room access.",
                formal="has_access:alice:server_room",
                channel=ClueChannel.RECORD,
                role="required",
                scene_id="sc1",
                reveal_order=2,
            ),
            VisibleFact(
                id="f3",
                text="Cara has server-room access.",
                formal="has_access:cara:server_room",
                channel=ClueChannel.RECORD,
                role="required",
                scene_id="sc1",
                reveal_order=3,
            ),
            VisibleFact(
                id="f4",
                text="The reboot requires holding the master badge.",
                formal="requires_item:master_badge",
                channel=ClueChannel.RULE_APPLICATION,
                role="required",
                scene_id="sc2",
                reveal_order=4,
            ),
            VisibleFact(
                id="f5",
                text="At 09:20 Alice held the master badge.",
                formal="holds:alice:master_badge",
                channel=ClueChannel.OBSERVATION,
                role="required",
                scene_id="sc2",
                reveal_order=5,
            ),
            VisibleFact(
                id="f6",
                text="Cara did not hold the badge after lending it.",
                formal="eliminated:cara",
                channel=ClueChannel.STATEMENT,
                role="required",
                scene_id="sc2",
                reveal_order=6,
            ),
            VisibleFact(
                id="f7",
                text="Ben was in the lobby and lacked server access.",
                formal="eliminated:ben",
                channel=ClueChannel.OBSERVATION,
                role="required",
                scene_id="sc3",
                reveal_order=7,
            ),
            VisibleFact(
                id="f8",
                text="Drew remained at reception.",
                formal="eliminated:drew",
                channel=ClueChannel.OBSERVATION,
                role="required",
                scene_id="sc3",
                reveal_order=8,
            ),
            VisibleFact(
                id="d1",
                text="The lobby coffee machine failed at 08:55.",
                formal="distractor:coffee",
                channel=ClueChannel.RECORD,
                role="distractor",
                scene_id="sc1",
                reveal_order=9,
            ),
        ],
    )


def make_underdetermined_visible(world: WorldSpec) -> VisibleTheory:
    """Access constraint only — Alice and Cara both survive."""
    vis = make_unique_visible(world)
    keep = {"f1", "f2", "f3", "d1"}
    facts = [f for f in vis.facts if f.id in keep]
    return VisibleTheory(id="vis-office-under", world_id=world.id, facts=facts)


def test_world_analysis_sat() -> None:
    world = load_world()
    report = WorldSolver().analyze_world(world)
    assert report.satisfiable
    assert report.target_truth == "alice"
    assert "e_reboot" in report.causal_trace


def test_disclosure_unique() -> None:
    world = load_world()
    vis = make_unique_visible(world)
    report = WorldSolver().analyze_disclosure(world, vis)
    assert report.unique
    assert report.answer == "alice"
    assert report.canonical_proof
    assert "f5" in report.minimal_support or "f1" in report.minimal_support


def test_disclosure_underdetermined() -> None:
    world = load_world()
    vis = make_underdetermined_visible(world)
    report = WorldSolver().analyze_disclosure(world, vis)
    assert report.unique is False
    assert "alice" in report.alternative_answers


def test_counterfactual_disables_badge_loan() -> None:
    world = load_world()
    cf = WorldSolver().analyze_counterfactual(world)
    assert cf is not None
    assert cf.answer == "none"
    assert "e_reboot" not in cf.causal_trace


def test_falsifier_against_ben() -> None:
    world = load_world()
    vis = make_unique_visible(world)
    report = WorldSolver().analyze_falsifier(world, vis, "ben")
    assert report.status == "contradicted"
    assert report.minimal_contradictory_set
