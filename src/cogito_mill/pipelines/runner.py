"""One-item and batch runners."""

from __future__ import annotations

from typing import Any

from cogito_mill.domain.run import RunStatus
from cogito_mill.pipelines.graph import build_mill_graph


def generate_one(
    *,
    seed: int,
    provider: str = "azure",
    output_root: str = "data",
    difficulty: str = "hard",
    n_suspects: int = 4,
    n_distractors: int = 4,
    target_hops: int = 5,
) -> dict[str, Any]:
    graph = build_mill_graph()
    result = graph.invoke(
        {
            "provider_family": provider,
            "output_root": output_root,
            "meta": {
                "seed": seed,
                "difficulty": difficulty,
                "n_suspects": n_suspects,
                "n_distractors": n_distractors,
                "target_hops": target_hops,
            },
        }
    )
    status = result.get("status", RunStatus.REJECTED)
    accepted = result.get("accepted")
    return {
        "run_id": result.get("run_id"),
        "status": status.value if hasattr(status, "value") else status,
        "item_id": accepted.id if accepted is not None else None,
        "artifact_dir": result.get("manifest").artifact_dir if result.get("manifest") else None,
        "errors": result.get("errors", []),
        "accepted": accepted,
    }


def generate_batch(
    *,
    n: int,
    seeds_from: int = 1000,
    provider: str = "azure",
    output_root: str = "data",
    difficulty: str = "hard",
    n_suspects: int = 4,
    n_distractors: int = 4,
    max_attempts: int | None = None,
) -> dict[str, Any]:
    attempts_limit = max_attempts or max(n * 2, n + 10)
    accepted = 0
    rejected = 0
    results: list[dict[str, Any]] = []
    seed = seeds_from
    attempts = 0
    while accepted < n and attempts < attempts_limit:
        one = generate_one(
            seed=seed,
            provider=provider,
            output_root=output_root,
            difficulty=difficulty,
            n_suspects=n_suspects,
            n_distractors=n_distractors,
        )
        attempts += 1
        seed += 1
        results.append({k: v for k, v in one.items() if k != "accepted"})
        if one["status"] == RunStatus.ACCEPTED.value:
            accepted += 1
        else:
            rejected += 1
    return {
        "accepted": accepted,
        "rejected": rejected,
        "attempts": attempts,
        "results": results,
    }
