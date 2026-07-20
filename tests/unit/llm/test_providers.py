import pytest

from cogito_mill.config import Settings
from cogito_mill.llm.providers import build_azure_chat, build_chat, build_glm_chat


def _azure_settings(**overrides: str) -> Settings:
    base = {
        "azure_openai_api_key": "test-key",
        "azure_openai_endpoint": "https://agents-patterns-lab-oai.openai.azure.com/",
        "azure_openai_api_version": "2025-04-01-preview",
        "azure_openai_writer_deployment": "gpt-5.6-luna-stories",
        "azure_openai_judge_deployment": "gpt-5.6-terra-stories",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def _glm_settings(**overrides: str) -> Settings:
    base = {
        "glm_api_key": "test-glm-key",
        "glm_base_url": "https://api.z.ai/api/coding/paas/v4/",
        "glm_writer_deployment": "glm-5.1",
        "glm_judge_deployment": "glm-5.2",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def test_build_chat_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        build_chat("nope")


def test_build_azure_chat_writer_uses_writer_deployment() -> None:
    chat = build_azure_chat(role="writer", settings=_azure_settings())
    assert chat.deployment_name == "gpt-5.6-luna-stories"


def test_build_azure_chat_judge_uses_judge_deployment() -> None:
    chat = build_azure_chat(role="judge", settings=_azure_settings())
    assert chat.deployment_name == "gpt-5.6-terra-stories"


def test_build_azure_chat_writer_requires_writer_deployment() -> None:
    settings = _azure_settings(azure_openai_writer_deployment="")
    with pytest.raises(ValueError, match="AZURE_OPENAI_WRITER_DEPLOYMENT"):
        build_azure_chat(role="writer", settings=settings)


def test_build_azure_chat_judge_requires_judge_deployment() -> None:
    settings = _azure_settings(azure_openai_judge_deployment="")
    with pytest.raises(ValueError, match="AZURE_OPENAI_JUDGE_DEPLOYMENT"):
        build_azure_chat(role="judge", settings=settings)


def test_build_chat_azure_passes_role() -> None:
    chat = build_chat("azure", role="judge", settings=_azure_settings())
    assert chat.deployment_name == "gpt-5.6-terra-stories"


def test_build_glm_chat_writer_uses_writer_model() -> None:
    chat = build_glm_chat(role="writer", settings=_glm_settings())
    assert chat.model_name == "glm-5.1"


def test_build_glm_chat_judge_uses_judge_model() -> None:
    chat = build_glm_chat(role="judge", settings=_glm_settings())
    assert chat.model_name == "glm-5.2"


def test_build_glm_chat_requires_role_deployment() -> None:
    settings = _glm_settings(glm_writer_deployment="")
    with pytest.raises(ValueError, match="GLM_WRITER_DEPLOYMENT"):
        build_glm_chat(role="writer", settings=settings)
