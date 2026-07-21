"""Blind evaluation against a chat model."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from cogito_mill.datasets.pack import pack_hub_items
from cogito_mill.eval.score import normalize_answer, score_exact_any
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
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def _iter_qa(row: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a hub row into scored QA units (supports multi-question items)."""
    nested = row.get("questions") or []
    if nested:
        out = []
        for q in nested:
            variants = q.get("gold_answer_variants") or [q.get("gold_answer", "")]
            out.append(
                {
                    "qa_id": q.get("id", "q"),
                    "question": q["question"],
                    "gold_answer": q.get("gold_answer", ""),
                    "gold_answer_variants": variants,
                    "question_type": q.get("question_type", "main"),
                }
            )
        return out
    variants = row.get("gold_answer_variants") or [row.get("gold_answer", "")]
    return [
        {
            "qa_id": "q_main",
            "question": row["question"],
            "gold_answer": row.get("gold_answer", ""),
            "gold_answer_variants": variants,
            "question_type": "main",
        }
    ]


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
    total_qa = 0
    first_only = 0
    for row in rows:
        for qa in _iter_qa(row):
            total_qa += 1
            prompt = (
                "You are solving a narrative deduction puzzle.\n"
                "Read the story and answer the question exactly as asked.\n"
                "If the question asks for a full name, give given name and surname.\n"
                "If the question asks for a badge code, give the exact code only.\n"
                "If nobody qualifies, answer exactly: none\n"
                "Respond with a single line in the form FINAL_ANSWER: <answer>.\n\n"
                f"STORY:\n{row['story']}\n\n"
                f"QUESTION:\n{qa['question']}\n"
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
            variants = qa["gold_answer_variants"]
            ok = score_exact_any(pred, variants)
            correct += int(ok)
            gold_parts = normalize_answer(qa["gold_answer"]).split()
            pred_norm = normalize_answer(pred)
            if gold_parts and pred_norm == gold_parts[0] and not ok:
                first_only += 1
            predictions.append(
                {
                    "id": row["id"],
                    "qa_id": qa["qa_id"],
                    "question_type": qa["question_type"],
                    "question": qa["question"],
                    "gold_answer": qa["gold_answer"],
                    "gold_answer_variants": variants,
                    "prediction": pred,
                    "normalized_prediction": pred_norm,
                    "normalized_gold": normalize_answer(qa["gold_answer"]),
                    "correct": ok,
                    "raw": raw[:2000],
                }
            )

    accuracy = correct / total_qa if total_qa else 0.0
    main_preds = [p for p in predictions if p.get("question_type") == "main"]
    main_correct = sum(1 for p in main_preds if p["correct"])
    main_accuracy = main_correct / len(main_preds) if main_preds else 0.0
    eval_id = f"eval-{int(time.time())}"
    out_dir = Path(output_root) / "processed" / "evals" / eval_id
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "eval_id": eval_id,
        "n_stories": len(rows),
        "n": total_qa,
        "correct": correct,
        "accuracy": accuracy,
        "main_n": len(main_preds),
        "main_correct": main_correct,
        "main_accuracy": main_accuracy,
        "first_name_only_rate": first_only / total_qa if total_qa else 0.0,
        "solver_provider": solver_provider,
        "dataset": dataset if local_dir is None else local_dir,
        "config": config,
        "max_accuracy_gate": 0.30,
        "passed_hardness_gate": main_accuracy <= 0.30,
    }
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "predictions.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in predictions) + "\n",
        encoding="utf-8",
    )
    report["artifact_dir"] = str(out_dir)
    return report
