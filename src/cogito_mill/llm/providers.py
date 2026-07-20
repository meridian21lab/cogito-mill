"""LLM provider factories (Azure OpenAI, GLM)."""

from __future__ import annotations

from typing import Any, Literal

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from cogito_mill.config.settings import Settings, get_settings

MillRole = Literal["writer", "judge"]


def build_azure_chat(
    role: MillRole = "writer",
    settings: Settings | None = None,
) -> AzureChatOpenAI:
    """Build Azure chat for a mill role.

    - ``writer``: cheaper / less capable deployment (story generation)
    - ``judge``: stronger deployment (verification / critique)
    """
    cfg = settings or get_settings()
    deployment = (
        cfg.azure_openai_writer_deployment
        if role == "writer"
        else cfg.azure_openai_judge_deployment
    )
    env_name = (
        "AZURE_OPENAI_WRITER_DEPLOYMENT"
        if role == "writer"
        else "AZURE_OPENAI_JUDGE_DEPLOYMENT"
    )
    missing = (
        not cfg.azure_openai_api_key
        or not cfg.azure_openai_endpoint
        or not deployment
    )
    if missing:
        raise ValueError(
            "Azure OpenAI requires AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, "
            f"and {env_name}"
        )
    return AzureChatOpenAI(
        api_key=cfg.azure_openai_api_key,
        azure_endpoint=cfg.azure_openai_endpoint,
        api_version=cfg.azure_openai_api_version,
        azure_deployment=deployment,
    )


def build_glm_chat(
    role: MillRole = "writer",
    settings: Settings | None = None,
) -> ChatOpenAI:
    """GLM via OpenAI-compatible HTTP API (role-specific model ids)."""
    cfg = settings or get_settings()
    model = (
        cfg.glm_writer_deployment if role == "writer" else cfg.glm_judge_deployment
    )
    env_name = (
        "GLM_WRITER_DEPLOYMENT" if role == "writer" else "GLM_JUDGE_DEPLOYMENT"
    )
    if not cfg.glm_api_key:
        raise ValueError("GLM requires GLM_API_KEY")
    if not model:
        raise ValueError(f"GLM requires {env_name}")
    return ChatOpenAI(
        api_key=cfg.glm_api_key,
        base_url=cfg.glm_base_url,
        model=model,
    )


def build_chat(
    provider: str = "azure",
    *,
    role: MillRole = "writer",
    settings: Settings | None = None,
) -> Any:
    if provider == "azure":
        return build_azure_chat(role=role, settings=settings)
    if provider == "glm":
        return build_glm_chat(role=role, settings=settings)
    raise ValueError(f"Unknown provider: {provider!r} (expected 'azure' or 'glm')")


__all__ = ["MillRole", "build_azure_chat", "build_glm_chat", "build_chat"]
