"""Dataset package exports."""

from __future__ import annotations

DEFAULT_HF_NAMESPACE = "ksopyla"


def hub_dataset_id(name: str, namespace: str = DEFAULT_HF_NAMESPACE) -> str:
    return f"{namespace}/{name}"


__all__ = ["DEFAULT_HF_NAMESPACE", "hub_dataset_id"]
