"""Objective pack-level narration and diversity gates."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from itertools import combinations
from typing import Any


def assess_dataset(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("quality assessment requires at least one row")
    narration = [_narration(row["story"]) for row in rows]
    stories = [row["story"] for row in rows]
    pairs = [
        _jaccard(_shingles(left), _shingles(right)) for left, right in combinations(stories, 2)
    ]
    template_counts = Counter(row.get("template_id") or "unknown" for row in rows)
    setting_counts = Counter(str(row.get("setting_family", "unknown")) for row in rows)
    main_stems = Counter(_normalize(row["question"]) for row in rows)
    openings = {" ".join(_normalize(story).split()[:24]) for story in stories}
    n = len(rows)
    narration_passes = sum(item["passed"] for item in narration)
    narration_gate = narration_passes == n if n < 100 else narration_passes / n >= 0.95
    min_templates = 4 if n < 100 else 6
    min_effective = 3.5 if n < 100 else 5.0
    max_template_share = 0.34 if n < 100 else 0.20
    min_settings = 5 if n < 100 else 6
    p95_similarity = _percentile(pairs, 0.95)
    exact_hashes = [hashlib.sha256(_normalize(story).encode()).hexdigest() for story in stories]
    exact_duplicates = n - len(set(exact_hashes))
    template_effective = _effective_count(template_counts)
    template_max_share = max(template_counts.values()) / n
    setting_entropy = _normalized_entropy(setting_counts)
    unique_opening_rate = len(openings) / n
    unique_stems = len(main_stems)
    stem_max_share = max(main_stems.values()) / n
    gates = {
        "narration": narration_gate,
        "no_exact_duplicates": exact_duplicates == 0,
        "template_count": len(template_counts) >= min_templates,
        "template_effective_count": template_effective >= min_effective,
        "template_max_share": template_max_share <= max_template_share,
        "setting_coverage": len(setting_counts) >= min_settings,
        "setting_entropy": setting_entropy >= 0.85,
        "surface_similarity_p95": p95_similarity <= 0.65,
        "unique_openings": unique_opening_rate >= 0.80,
        "question_stems": unique_stems >= min(8, n),
        "question_stem_max_share": stem_max_share <= 0.20,
        "structural_hops": all(int(row.get("n_hops", 0)) >= 10 for row in rows),
    }
    return {
        "n": n,
        "passed": all(gates.values()),
        "gates": gates,
        "narration": {
            "passed": narration_passes,
            "failed": n - narration_passes,
            "min_words": min(item["words"] for item in narration),
            "median_words": _percentile([item["words"] for item in narration], 0.50),
            "max_words": max(item["words"] for item in narration),
        },
        "diversity": {
            "exact_duplicates": exact_duplicates,
            "template_counts": dict(template_counts),
            "template_effective_count": template_effective,
            "template_max_share": template_max_share,
            "setting_counts": dict(setting_counts),
            "setting_entropy": setting_entropy,
            "unique_opening_rate": unique_opening_rate,
            "unique_main_question_stems": unique_stems,
            "main_question_stem_max_share": stem_max_share,
            "pairwise_5_shingle_p95": p95_similarity,
            "pairwise_5_shingle_max": max(pairs, default=0.0),
        },
    }


def _narration(text: str) -> dict[str, Any]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    words = re.findall(r"\b[\w'-]+\b", text)
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    sentence_lengths = [len(re.findall(r"\b[\w'-]+\b", sentence)) for sentence in sentences]
    passed = (
        len(paragraphs) >= 5
        and 500 <= len(words) <= 2500
        and _percentile(sentence_lengths, 0.95) <= 45
        and text.casefold().count("personnel index:") <= 1
        and len(re.findall(r"\bEMP-\d+\b", text, flags=re.IGNORECASE)) <= 6
    )
    return {
        "passed": passed,
        "paragraphs": len(paragraphs),
        "words": len(words),
        "sentence_p95_words": _percentile(sentence_lengths, 0.95),
    }


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _shingles(text: str, size: int = 5) -> set[tuple[str, ...]]:
    tokens = _normalize(text).split()
    return {tuple(tokens[index : index + size]) for index in range(max(0, len(tokens) - size + 1))}


def _jaccard(left: set[tuple[str, ...]], right: set[tuple[str, ...]]) -> float:
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def _percentile(values: list[int] | list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = math.ceil(quantile * len(ordered)) - 1
    return float(ordered[max(0, index)])


def _effective_count(counts: Counter[str]) -> float:
    total = sum(counts.values())
    return 1.0 / sum((count / total) ** 2 for count in counts.values())


def _normalized_entropy(counts: Counter[str]) -> float:
    if len(counts) <= 1:
        return 0.0
    total = sum(counts.values())
    entropy = -sum((count / total) * math.log(count / total) for count in counts.values())
    return entropy / math.log(len(counts))


__all__ = ["assess_dataset"]
