"""Dataset schemas, local packing, and Hugging Face Hub publish helpers."""

from __future__ import annotations

DEFAULT_HF_NAMESPACE = "ksopyla"


def hub_dataset_id(name: str, namespace: str = DEFAULT_HF_NAMESPACE) -> str:
    return f"{namespace}/{name}"
