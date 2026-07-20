"""Blind evaluation against a chat model."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from cogito_mill.datasets.pack import pack_hub_items
from cogito_mill.eval.score import normalize_answer, score_exact
from cogito_mill.llm.providers import build_chat


def _load_rows(
    *,
    dataset: str,
    config: str,
    split: str,
    limit: int | None,
    local_dir: str | None,
) -> list[dict[str, Any]]:
    if local_dir:
        root = Path(local_dir)
        if root.is_file() and root.suffix == ".jsonl":
            rows = [
                json.loads(line)
                for line in root.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            rows = pack_hub_items(root)
    else:
        from datasets import load_dataset

        ds = load_dataset(dataset, config, split=split)
        rows = [dict(r) for r in ds]
    if limit is not None:
        rows = rows[:limit]
    return rows


def _extract_answer(text: str) -> str:
    text = text.strip()
    m = re.search(r"FINAL_ANSWER:\s*(.+)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip().splitlines()[0].strip()
    # fallback: last non-empty line
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def evaluate_dataset(
    *,
    dataset: str = "ksopyla/long-story-short-pilot",
    config: str = "pilot_v0",
    split: str = "train",
    limit: int | None = 50,
    solver_provider: str = "azure",
    local_dir: str | None = None,
    output_root: str = "data",
) -> dict[str, Any]:
    rows = _load_rows(
        dataset=dataset,
        config=config,
        split=split,
        limit=limit,
        local_dir=local_dir,
    )
    if not rows:
        raise ValueError("no evaluation rows found")

    chat = build_chat(solver_provider, role="writer")
    predictions: list[dict[str, Any]] = []
    correct = 0
    for row in rows:
        prompt = (
            "You are solving a narrative deduction puzzle.\n"
            "Read the story and answer the question.\n"
            "Respond with a single line in the form FINAL_ANSWER: <name>.\n\n"
            f"STORY:\n{row['story']}\n\n"
            f"QUESTION:\n{row['question']}\n"
        )
        try:
            msg = chat.invoke(prompt)
            raw = getattr(msg, "content", str(msg))
            if isinstance(raw, list):
                raw = " ".join(str(x) for x in raw)
            pred = _extract_answer(str(raw))
        except Exception as exc:  # noqa: BLE001 - record transport failures
            pred = ""
            raw = f"ERROR: {exc}"
        ok = score_exact(pred, row["gold_answer"])
        correct += int(ok)
        predictions.append(
            {
                "id": row["id"],
                "gold_answer": row["gold_answer"],
                "prediction": pred,
                "normalized_prediction": normalize_answer(pred),
                "normalized_gold": normalize_answer(row["gold_answer"]),
                "correct": ok,
                "raw": raw[:2000],
            }
        )

    accuracy = correct / len(rows)
    eval_id = f"eval-{int(time.time())}"
    out_dir = Path(output_root) / "processed" / "evals" / eval_id
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "eval_id": eval_id,
        "n": len(rows),
        "correct": correct,
        "accuracy": accuracy,
        "solver_provider": solver_provider,
        "dataset": dataset if local_dir is None else local_dir,
        "config": config,
        "max_accuracy_gate": 0.30,
        "passed_hardness_gate": accuracy <= 0.30,
    }
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "predictions.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in predictions) + "\n",
        encoding="utf-8",
    )
    report["artifact_dir"] = str(out_dir)
    return report
