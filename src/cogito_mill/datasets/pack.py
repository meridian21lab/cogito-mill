"""Pack accepted hub items from processed run directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cogito_mill.domain.appendix import SolverAppendix
from cogito_mill.domain.run import PilotHubItem


def pack_hub_items(processed_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not processed_root.exists():
        return rows
    for path in sorted(processed_root.glob("*/hub-item.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        item = PilotHubItem.model_validate(data)
        rows.append(item.model_dump(mode="json"))
    return rows


def pack_appendix_items(processed_root: Path) -> list[dict[str, Any]]:
    """Pack companion solver appendices (not part of the thin Hub schema)."""
    rows: list[dict[str, Any]] = []
    if not processed_root.exists():
        return rows
    for path in sorted(processed_root.glob("*/reasoning-appendix.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        appendix = SolverAppendix.model_validate(data)
        rows.append(appendix.model_dump(mode="json"))
    return rows


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path
