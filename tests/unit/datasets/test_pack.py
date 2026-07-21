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
        "gold_answer_variants",
        "questions",
        "n_hops",
        "setting_family",
        "difficulty_bucket",
    }
    assert 2 <= len(rows[0]["questions"]) <= 4
    assert 1 <= len(rows[0]["gold_answer_variants"]) <= 3
    # json serializable
    json.dumps(rows[0])
