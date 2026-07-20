"""Filesystem artifact persistence."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cogito_mill.domain.run import AcceptedItem, RunManifest, RunStatus


def _write_json(path: Path, payload: dict[str, Any] | BaseModel) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    text = json.dumps(data, indent=2, sort_keys=True)
    digest = hashlib.sha256(text.encode()).hexdigest()
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".`tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return digest


class ArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def run_dirs(self, run_id: str) -> dict[str, Path]:
        return {
            "raw": self.root / "raw" / run_id,
            "interim": self.root / "interim" / run_id,
            "processed": self.root / "processed" / run_id,
        }

    def write_stage(self, run_id: str, stage: str, payload: BaseModel | dict[str, Any]) -> str:
        path = self.run_dirs(run_id)["interim"] / f"{stage}.json"
        return _write_json(path, payload)

    def write_raw(self, run_id: str, name: str, payload: BaseModel | dict[str, Any]) -> str:
        path = self.run_dirs(run_id)["raw"] / name
        return _write_json(path, payload)

    def write_manifest(self, manifest: RunManifest) -> Path:
        dirs = self.run_dirs(manifest.run_id)
        dirs["raw"].mkdir(parents=True, exist_ok=True)
        path = dirs["raw"] / "manifest.json"
        _write_json(path, manifest)
        return path

    def promote_accepted(self, item: AcceptedItem, report: dict[str, Any]) -> Path:
        dirs = self.run_dirs(item.run_id)
        out = dirs["processed"]
        out.mkdir(parents=True, exist_ok=True)
        _write_json(out / "reasoning-item.json", item)
        _write_json(out / "hub-item.json", item.to_hub_item())
        _write_json(out / "acceptance-report.json", report)
        return out

    def list_accepted(self) -> list[Path]:
        processed = self.root / "processed"
        if not processed.exists():
            return []
        return sorted(processed.glob("*/hub-item.json"))


def new_run_id(seed: int) -> str:
    return f"run-{seed:08d}"


def initial_manifest(
    *,
    run_id: str,
    seed: int,
    provider_family: str,
    recipe_id: str,
) -> RunManifest:
    return RunManifest(
        run_id=run_id,
        status=RunStatus.RUNNING,
        seed=seed,
        provider_family=provider_family,
        recipe_id=recipe_id,
    )
