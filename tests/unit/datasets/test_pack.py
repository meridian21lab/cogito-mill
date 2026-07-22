"""Pack helper tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

from cogito_mill.datasets.pack import pack_appendix_items, pack_hub_items
from cogito_mill.pipelines import generate_one


def test_pack_after_generate(tmp_path: Path) -> None:
    result = generate_one(seed=7, output_root=str(tmp_path))
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
    assert 10 <= rows[0]["n_hops"] <= 80
    assert not any(re.search(r"-\d+$", q["gold_answer"]) for q in rows[0]["questions"])
    # json serializable
    json.dumps(rows[0])
    appendices = pack_appendix_items(tmp_path / "processed")
    assert len(appendices) == 1
    assert appendices[0]["id"] == rows[0]["id"]
    assert appendices[0]["mechanism"] == "provenance_custody_dag"
    assert len(appendices[0]["provenance_states"]) == 13
    assert set(appendices[0]["opportunity"].values()) == {True}
    assert (tmp_path / "processed" / result["run_id"] / "reasoning-appendix.json").exists()
