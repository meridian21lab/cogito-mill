"""Application settings loaded from environment / `.env`."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_azure_endpoint(endpoint: str | None) -> str | None:
    """Return Azure OpenAI resource root only (no /openai path or query)."""
    if endpoint is None:
        return None
    value = endpoint.strip()
    if not value:
        return value
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    return f"{parsed.scheme}://{parsed.netloc}/"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure OpenAI — shared resource
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2024-12-01-preview"
    # Role-specific deployments (same resource, different model SKUs)
    azure_openai_writer_deployment: str | None = None
    azure_openai_judge_deployment: str | None = None
    azure_openai_embedding_deployment: str | None = None

    # GLM (OpenAI-compatible) — role-specific model ids
    glm_api_key: str | None = None
    glm_base_url: str = "https://api.z.ai/api/coding/paas/v4/"
    glm_writer_deployment: str | None = None
    glm_judge_deployment: str | None = None

    # Hugging Face
    hf_token: str | None = None
    hf_dataset_namespace: str = "ksopyla"

    @field_validator(
        "azure_openai_api_key",
        "azure_openai_api_version",
        "azure_openai_writer_deployment",
        "azure_openai_judge_deployment",
        "azure_openai_embedding_deployment",
        "glm_api_key",
        "glm_base_url",
        "glm_writer_deployment",
        "glm_judge_deployment",
        "hf_token",
        mode="before",
    )
    @classmethod
    def _strip_str(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("azure_openai_endpoint", mode="before")
    @classmethod
    def _normalize_endpoint(cls, value: object) -> object:
        if isinstance(value, str) or value is None:
            return normalize_azure_endpoint(value)
        return value


def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings", "normalize_azure_endpoint"]
