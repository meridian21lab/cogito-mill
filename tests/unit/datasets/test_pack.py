"""Pack helper tests."""

from __future__ import annotations

import json
from pathlib import Path

from cogito_mill.datasets.pack import pack_hub_items
from cogito_mill.pipelines import generate_one


def test_pack_after_generate(tmp_path: Path) -> None:
    generate_one(seed=7, output_root=str(tmp_path))
    rows = pack_hub_items(tmp_path / "processed")
    assert len(rows) == 1
    assert set(rows[0]) >= {
        "id",
        "story",
        "question",
        "gold_answer",
        "n_hops",
        "setting_family",
        "difficulty_bucket",
    }
    # json serializable
    json.dumps(rows[0])
