"""Application settings loaded from environment / `.env`."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure OpenAI
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment: str | None = None
    azure_openai_embedding_deployment: str | None = None

    # GLM (OpenAI-compatible)
    glm_api_key: str | None = None
    glm_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    glm_model: str = "glm-4.5"

    # Hugging Face
    hf_token: str | None = None
    hf_dataset_namespace: str = "ksopyla"


def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
