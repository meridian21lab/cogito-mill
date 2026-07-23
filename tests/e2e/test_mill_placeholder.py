"""Offline E2E: handwritten template path through the compiled graph."""

from __future__ import annotations

from pathlib import Path

import pytest

from cogito_mill.domain.run import RunStatus
from cogito_mill.pipelines import generate_one


@pytest.mark.e2e
def test_e2e_offline_generate_one(tmp_path: Path) -> None:
    result = generate_one(seed=99, output_root=str(tmp_path), n_suspects=6, n_distractors=5)
    assert result["status"] == RunStatus.ACCEPTED.value
    assert result["accepted"] is not None
    assert len(result["accepted"].story) > 200
