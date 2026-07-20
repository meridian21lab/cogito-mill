"""Pipeline integration tests (offline)."""

from __future__ import annotations

from pathlib import Path

from cogito_mill.domain.run import RunStatus
from cogito_mill.pipelines import generate_batch, generate_one


def test_generate_one_accepted(tmp_path: Path) -> None:
    result = generate_one(seed=42, output_root=str(tmp_path), provider="azure")
    assert result["status"] == RunStatus.ACCEPTED.value
    assert result["item_id"]
    assert (tmp_path / "processed" / result["run_id"] / "hub-item.json").exists()
    assert (tmp_path / "processed" / result["run_id"] / "reasoning-item.json").exists()


def test_generate_batch_small(tmp_path: Path) -> None:
    summary = generate_batch(
        n=3,
        seeds_from=200,
        output_root=str(tmp_path),
        n_suspects=4,
        n_distractors=3,
    )
    assert summary["accepted"] == 3
    assert summary["rejected"] == 0
