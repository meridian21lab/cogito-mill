#!/usr/bin/env python3
"""Send a prepared quality-assessment prompt to the external Azure judge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr

from cogito_mill.config.settings import get_settings

SYSTEM_PROMPT = """You are Cogito Mill's independent high-level dataset quality judge.
Evaluate the supplied evidence packet and the parent's observations, not the generation agents.
Confirm supported observations, challenge unsupported ones, and identify overlooked weaknesses.
Deterministic gates and recorded metrics are authoritative within their measured scope. Do not
recompute formal truth or timeline arithmetic. Separate measured evidence from inference and
missing evidence. Prefer semantic and strategic findings over an exhaustive metric review.

Always check for these high-priority weaknesses when stories are present:
1. Formulaic ledger language shared across items (protocol active, status scales, coefficients,
   modulo/checksum/tally procedures, six-stream enumerations, "counted as N" maps).
2. Arithmetic-only hardness that a human cannot map as timeline/causal logic.
3. Middle sections of jargon with little narrative meaning, or forced difficulty padding.
4. Cross-item monotony: same incident→mapping→enumeration skeleton with only numbers swapped.
5. Setting/name incoherence and artificial twin-name suffixes.
6. Counterfactuals that only retarget an opaque key instead of minimal evidence edits.

Stories should read as human mysteries with people, places, clock times, travel, and alibis.
A strong item lets a careful reader build a timeline map and eliminate candidates without
performing modular arithmetic. Prefer ordinary activity carrying evidence over investigator
recitation of scales and coefficients.
Return a concise report with: verdict; confirmed/challenged/new observations; up to three
weaknesses; and one focused next experiment. Cite item IDs and short exact story/question excerpts
for qualitative claims. Do not reveal chain-of-thought."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deployment",
        default="gpt-5.6-terra-stories",
        help="Azure OpenAI deployment name",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Read the evidence packet from this file instead of stdin",
    )
    return parser


def _response_text(content: object) -> str:
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


def main() -> int:
    args = _parser().parse_args()
    prompt = (
        args.prompt_file.read_text(encoding="utf-8")
        if args.prompt_file
        else sys.stdin.read()
    )
    if not prompt.strip():
        raise ValueError("quality judge prompt is empty")

    settings = get_settings()
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT are required")

    chat = AzureChatOpenAI(
        api_key=SecretStr(settings.azure_openai_api_key),
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_deployment=args.deployment,
        reasoning_effort="high",
        max_retries=2,
        timeout=300,
    )
    response = chat.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )
    print(_response_text(response.content))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
