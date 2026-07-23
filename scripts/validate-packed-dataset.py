#!/usr/bin/env python3
"""Validate packed JSONL integrity against the frozen Hub JSON Schema."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate every packed row, unique IDs, and report immutable hashes."
    )
    parser.add_argument("jsonl", type=Path, help="Packed dataset JSONL")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/reasoning-item.schema.json"),
        help="JSON Schema (default: schemas/reasoning-item.schema.json)",
    )
    parser.add_argument("--output", type=Path, help="Optional integrity report JSON")
    return parser


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_dataset_hash(rows: list[dict[str, Any]]) -> str:
    payload = "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    args = _parser().parse_args()
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []

    if not args.jsonl.is_file():
        print(f"error: packed dataset not found: {args.jsonl}", file=sys.stderr)
        return 4
    if not args.schema.is_file():
        print(f"error: schema not found: {args.schema}", file=sys.stderr)
        return 4

    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for line_number, line in enumerate(
        args.jsonl.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "path": "$", "message": str(exc)})
            continue
        rows.append(row)
        for error in sorted(validator.iter_errors(row), key=lambda item: list(item.path)):
            path = "$" + "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
            )
            errors.append({"line": line_number, "path": path, "message": error.message})

    ids = [str(row.get("id", "")) for row in rows]
    id_counts = Counter(ids)
    duplicate_ids = sorted(item_id for item_id, count in id_counts.items() if count > 1)
    if duplicate_ids:
        errors.append(
            {
                "line": None,
                "path": "$.id",
                "message": f"duplicate item ids: {duplicate_ids}",
            }
        )
    if not rows:
        errors.append({"line": None, "path": "$", "message": "dataset has no rows"})

    report = {
        "valid": not errors,
        "n": len(rows),
        "unique_ids": len(set(ids)),
        "duplicate_ids": duplicate_ids,
        "jsonl": str(args.jsonl),
        "jsonl_sha256": _sha256(args.jsonl),
        "dataset_sha256": _canonical_dataset_hash(rows),
        "schema": str(args.schema),
        "schema_sha256": _sha256(args.schema),
        "errors": errors,
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["valid"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
