"""Unit tests for domain model validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cogito_mill.domain import (
    Entity,
    GenerationRecipe,
    SettingFamily,
    TargetClaim,
    WorldSpec,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "worlds" / "office_badge.json"


def test_office_badge_fixture_loads() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    world = WorldSpec.model_validate(data)
    assert world.answer_entity == "alice"
    assert world.intervention is not None
    assert len(world.candidate_answers) == 4


def test_world_rejects_unknown_answer_entity() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["answer_entity"] = "ghost"
    with pytest.raises(ValidationError):
        WorldSpec.model_validate(data)


def test_world_rejects_bad_relation_ref() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["relations"][0]["object"] = "nope"
    with pytest.raises(ValidationError):
        WorldSpec.model_validate(data)


def test_recipe_defaults() -> None:
    recipe = GenerationRecipe(
        id="r1",
        seed=7,
        setting_family=SettingFamily.WORKPLACE,
    )
    assert recipe.target_hops == 5
    assert recipe.require_causal is True


def test_entity_roundtrip() -> None:
    ent = Entity(id="a", type="person", label="A")
    assert Entity.model_validate(ent.model_dump()).label == "A"


def test_target_claim_shape() -> None:
    claim = TargetClaim(predicate="rebooted_by", arguments=["servers"], expected_value="alice")
    assert claim.expected_value == "alice"
