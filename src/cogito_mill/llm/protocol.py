"""Injectable structured-output model protocol."""

from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

from cogito_mill.llm.providers import MillRole, build_chat

T = TypeVar("T", bound=BaseModel)


class StructuredModel(Protocol):
    def invoke_structured(self, schema: type[T], prompt: str) -> T: ...


class FakeStructuredModel:
    """Deterministic fake returning preloaded payloads by role."""

    def __init__(self, payloads: dict[str, BaseModel] | None = None) -> None:
        self.payloads = payloads or {}
        self.calls: list[tuple[str, str]] = []

    def invoke_structured(self, schema: type[T], prompt: str) -> T:
        key = schema.__name__
        self.calls.append((key, prompt[:200]))
        if key not in self.payloads:
            raise KeyError(f"No fake payload for {key}")
        value = self.payloads[key]
        return schema.model_validate(value.model_dump())


class LangChainStructuredModel:
    def __init__(self, provider: str, role: MillRole) -> None:
        self._chat = build_chat(provider, role=role)
        self.provider = provider
        self.role = role

    def invoke_structured(self, schema: type[T], prompt: str) -> T:
        runnable = self._chat.with_structured_output(schema)
        result = runnable.invoke(prompt)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)


def build_structured_model(
    provider: str,
    role: MillRole,
    *,
    fake: StructuredModel | None = None,
) -> StructuredModel:
    if fake is not None:
        return fake
    return LangChainStructuredModel(provider, role)


__all__ = [
    "FakeStructuredModel",
    "LangChainStructuredModel",
    "StructuredModel",
    "build_structured_model",
]
