#!/usr/bin/env python3
"""Verify that every scored target field is invariant across satisfying CSP models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cogito_mill.domain.evidence import VisibleTheory
from cogito_mill.domain.world import WorldSpec
from cogito_mill.reasoning.constraints import target_tuples


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment_root", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def audit(experiment_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for visible_path in sorted((experiment_root / "interim").glob("run-*/visible-theory.json")):
        run_id = visible_path.parent.name
        hub_path = experiment_root / "processed" / run_id / "hub-item.json"
        world_path = visible_path.parent / "world.json"
        if not hub_path.exists() or not world_path.exists():
            continue
        visible = VisibleTheory.model_validate_json(visible_path.read_text(encoding="utf-8"))
        if visible.constraints is None:
            continue
        world = WorldSpec.model_validate_json(world_path.read_text(encoding="utf-8"))
        hub = json.loads(hub_path.read_text(encoding="utf-8"))
        questions = {question["id"]: question for question in hub["questions"]}
        tuples = target_tuples(visible.constraints)
        rendered = [
            {
                "person_id": item.person,
                "person": next(
                    entity.label for entity in world.entities if entity.id == item.person
                ),
                "place": item.place,
                "time": item.time,
            }
            for item in tuples
        ]
        expected = {
            "person": questions["q_main"]["gold_answer"],
            "place": questions["q_target_place"]["gold_answer"],
            "time": questions["q_target_time"]["gold_answer"],
        }
        passed = len(rendered) == 1 and all(
            rendered[0][field] == value for field, value in expected.items()
        )
        rows.append(
            {
                "id": hub["id"],
                "passed": passed,
                "n_target_tuples": len(rendered),
                "expected": expected,
                "satisfying_target_tuples": rendered,
            }
        )
    return {
        "n": len(rows),
        "passed": bool(rows) and all(row["passed"] for row in rows),
        "unique_target_tuples": sum(row["n_target_tuples"] == 1 for row in rows),
        "items": rows,
    }


def main() -> int:
    args = _parser().parse_args()
    report = audit(args.experiment_root)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["passed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
