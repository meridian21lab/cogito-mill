"""Application settings loaded from environment / `.env`."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


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


def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
