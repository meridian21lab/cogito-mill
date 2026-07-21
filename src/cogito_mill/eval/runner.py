"""Blind evaluation against a chat model."""

from __future__ import annotations

import hashlib
import json
import math
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
        from datasets import load_dataset  # type: ignore[import-untyped]

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
    main_only: bool = False,
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
    first_only_denominator = 0
    transport_errors = 0
    prompt_template = (
        "You are solving a narrative deduction puzzle.\n"
        "Read the story and answer the question exactly as asked.\n"
        "If the question asks for a full name, give given name and surname.\n"
        "If the question asks for a badge code, give the exact code only.\n"
        "If nobody qualifies, answer exactly: none\n"
        "Respond with a single line in the form FINAL_ANSWER: <answer>.\n\n"
    )
    for row in rows:
        qa_units = _iter_qa(row)
        if main_only:
            qa_units = [qa for qa in qa_units if qa["question_type"] == "main"]
        for qa in qa_units:
            total_qa += 1
            prompt = prompt_template + (f"STORY:\n{row['story']}\n\nQUESTION:\n{qa['question']}\n")
            try:
                msg = _invoke_with_retry(chat, prompt)
                raw = getattr(msg, "content", str(msg))
                if isinstance(raw, list):
                    raw = " ".join(str(x) for x in raw)
                pred = _extract_answer(str(raw))
            except Exception as exc:  # noqa: BLE001 - record transport failures
                transport_errors += 1
                raise RuntimeError(
                    f"solver transport failed for {row['id']}/{qa['qa_id']}"
                ) from exc
            variants = qa["gold_answer_variants"]
            ok = score_exact_any(pred, variants)
            correct += int(ok)
            gold_parts = normalize_answer(qa["gold_answer"]).split()
            pred_norm = normalize_answer(pred)
            if len(gold_parts) >= 2 and qa["gold_answer"].casefold() != "none":
                first_only_denominator += 1
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
    main_wilson_upper = _wilson_upper(main_correct, len(main_preds))
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
        "first_name_only_count": first_only,
        "first_name_only_n": first_only_denominator,
        "first_name_only_rate": (
            first_only / first_only_denominator if first_only_denominator else 0.0
        ),
        "transport_errors": transport_errors,
        "solver_provider": solver_provider,
        "dataset": dataset if local_dir is None else local_dir,
        "config": config,
        "max_accuracy_gate": 0.30,
        "passed_hardness_gate": main_accuracy <= 0.30,
        "main_accuracy_wilson_upper_95": main_wilson_upper,
        "passed_statistical_hardness_gate": main_wilson_upper <= 0.30,
        "dataset_sha256": hashlib.sha256(
            "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows).encode()
        ).hexdigest(),
        "prompt_sha256": hashlib.sha256(prompt_template.encode()).hexdigest(),
        "scorer_version": "pilot.v2",
    }
    (out_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "predictions.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in predictions) + "\n",
        encoding="utf-8",
    )
    report["artifact_dir"] = str(out_dir)
    return report


def _invoke_with_retry(chat: Any, prompt: str) -> Any:
    for attempt in range(3):
        try:
            return chat.invoke(prompt)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _wilson_upper(successes: int, total: int, z: float = 1.645) -> float:
    if total == 0:
        return 1.0
    observed = successes / total
    denominator = 1 + z**2 / total
    center = observed + z**2 / (2 * total)
    margin = z * math.sqrt(observed * (1 - observed) / total + z**2 / (4 * total**2))
    return (center + margin) / denominator
