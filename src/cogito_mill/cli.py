"""CLI entrypoint for Cogito Mill pilot commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _cmd_generate_one(args: argparse.Namespace) -> int:
    from cogito_mill.pipelines import generate_one

    result = generate_one(
        seed=args.seed,
        provider=args.provider,
        output_root=args.output_root,
        difficulty=args.difficulty,
        n_suspects=args.n_suspects,
        n_distractors=args.n_distractors,
    )
    printable = {k: v for k, v in result.items() if k != "accepted"}
    print(json.dumps(printable, indent=2))
    return 0 if result["status"] == "accepted" else 1


def _cmd_generate_batch(args: argparse.Namespace) -> int:
    from cogito_mill.pipelines import generate_batch

    summary = generate_batch(
        n=args.n,
        seeds_from=args.seeds_from,
        provider=args.provider,
        output_root=args.output_root,
        difficulty=args.difficulty,
        n_suspects=args.n_suspects,
        n_distractors=args.n_distractors,
        max_attempts=args.max_attempts,
    )
    print(
        json.dumps(
            {
                "accepted": summary["accepted"],
                "rejected": summary["rejected"],
                "attempts": summary["attempts"],
            },
            indent=2,
        )
    )
    return 0 if summary["accepted"] >= args.n else 1


def _cmd_publish(args: argparse.Namespace) -> int:
    from cogito_mill.datasets.hub import publish_pilot_dataset
    from cogito_mill.datasets.pack import pack_hub_items

    packed = pack_hub_items(Path(args.input))
    print(f"packed {len(packed)} items from {args.input}")
    if args.dry_run:
        out = Path(args.output_root) / "packed" / "pilot_v0.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as handle:
            for row in packed:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"wrote {out}")
        return 0
    url = publish_pilot_dataset(
        rows=packed,
        repo_id=args.repo,
        config=args.config,
        private=args.private,
    )
    print(url)
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    from cogito_mill.eval.runner import evaluate_dataset

    report = evaluate_dataset(
        dataset=args.dataset,
        config=args.config,
        split=args.split,
        limit=args.limit,
        solver_provider=args.solver_provider,
        local_dir=args.local_dir,
        output_root=args.output_root,
    )
    print(json.dumps(report, indent=2))
    acc = float(report.get("accuracy", 1.0))
    return 0 if acc <= args.max_accuracy else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cogito-mill")
    sub = parser.add_subparsers(dest="command", required=True)

    one = sub.add_parser("generate-one", help="Generate one verified pilot item")
    one.add_argument("--provider", default="azure", choices=["azure", "glm"])
    one.add_argument("--seed", type=int, default=42)
    one.add_argument("--output-root", default="data")
    one.add_argument("--difficulty", default="hard", choices=["medium", "hard", "very_hard"])
    one.add_argument("--n-suspects", type=int, default=4)
    one.add_argument("--n-distractors", type=int, default=4)
    one.set_defaults(func=_cmd_generate_one)

    batch = sub.add_parser("generate-batch", help="Generate N accepted pilot items")
    batch.add_argument("--provider", default="azure", choices=["azure", "glm"])
    batch.add_argument("--n", type=int, default=150)
    batch.add_argument("--seeds-from", type=int, default=1000)
    batch.add_argument("--output-root", default="data")
    batch.add_argument("--difficulty", default="hard", choices=["medium", "hard", "very_hard"])
    batch.add_argument("--n-suspects", type=int, default=5)
    batch.add_argument("--n-distractors", type=int, default=6)
    batch.add_argument("--max-attempts", type=int, default=None)
    batch.set_defaults(func=_cmd_generate_batch)

    pub = sub.add_parser("publish", help="Pack and publish pilot dataset to the Hub")
    pub.add_argument("--input", default="data/processed")
    pub.add_argument("--repo", default="ksopyla/long-story-short-pilot")
    pub.add_argument("--config", default="pilot_v0")
    pub.add_argument("--private", action=argparse.BooleanOptionalAction, default=True)
    pub.add_argument("--dry-run", action="store_true")
    pub.add_argument("--output-root", default="data")
    pub.set_defaults(func=_cmd_publish)

    ev = sub.add_parser("evaluate", help="Blind-evaluate a solver model on the pilot set")
    ev.add_argument("--dataset", default="ksopyla/long-story-short-pilot")
    ev.add_argument("--config", default="pilot_v0")
    ev.add_argument("--split", default="train")
    ev.add_argument("--limit", type=int, default=50)
    ev.add_argument("--solver-provider", default="azure", choices=["azure", "glm"])
    ev.add_argument("--local-dir", default=None, help="Evaluate from local packed JSONL")
    ev.add_argument("--output-root", default="data")
    ev.add_argument("--max-accuracy", type=float, default=0.30)
    ev.set_defaults(func=_cmd_evaluate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.func(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main(sys.argv[1:])
