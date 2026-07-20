"""LLM provider factories (Azure OpenAI, GLM)."""

from __future__ import annotations

from typing import Any

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from cogito_mill.config.settings import Settings, get_settings


def build_azure_chat(settings: Settings | None = None) -> AzureChatOpenAI:
    cfg = settings or get_settings()
    missing = (
        not cfg.azure_openai_api_key
        or not cfg.azure_openai_endpoint
        or not cfg.azure_openai_deployment
    )
    if missing:
        raise ValueError(
            "Azure OpenAI requires AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
            "and AZURE_OPENAI_DEPLOYMENT"
        )
    return AzureChatOpenAI(
        api_key=cfg.azure_openai_api_key,
        azure_endpoint=cfg.azure_openai_endpoint,
        api_version=cfg.azure_openai_api_version,
        azure_deployment=cfg.azure_openai_deployment,
    )


def build_glm_chat(settings: Settings | None = None) -> ChatOpenAI:
    """GLM via OpenAI-compatible HTTP API."""
    cfg = settings or get_settings()
    if not cfg.glm_api_key:
        raise ValueError("GLM requires GLM_API_KEY")
    return ChatOpenAI(
        api_key=cfg.glm_api_key,
        base_url=cfg.glm_base_url,
        model=cfg.glm_model,
    )


def build_chat(provider: str = "azure", settings: Settings | None = None) -> Any:
    if provider == "azure":
        return build_azure_chat(settings)
    if provider == "glm":
        return build_glm_chat(settings)
    raise ValueError(f"Unknown provider: {provider!r} (expected 'azure' or 'glm')")


__all__ = ["build_azure_chat", "build_glm_chat", "build_chat"]
