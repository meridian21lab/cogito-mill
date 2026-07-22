from cogito_mill.config import Settings, get_settings, normalize_azure_endpoint


def test_settings_defaults() -> None:
    settings = Settings(
        _env_file=None,
        azure_openai_api_key=None,
        azure_openai_endpoint=None,
        azure_openai_writer_deployment=None,
        azure_openai_judge_deployment=None,
        glm_writer_deployment=None,
        glm_judge_deployment=None,
    )
    assert settings.hf_dataset_namespace == "ksopyla"
    assert settings.glm_writer_deployment is None
    assert settings.glm_judge_deployment is None
    assert settings.azure_openai_writer_deployment is None
    assert settings.azure_openai_judge_deployment is None


def test_settings_loads_writer_and_judge_deployments() -> None:
    settings = Settings(
        _env_file=None,
        azure_openai_writer_deployment="gpt-5.6-luna-stories",
        azure_openai_judge_deployment="gpt-5.6-terra-stories",
        glm_writer_deployment="glm-5.1",
        glm_judge_deployment="glm-5.2",
    )
    assert settings.azure_openai_writer_deployment == "gpt-5.6-luna-stories"
    assert settings.azure_openai_judge_deployment == "gpt-5.6-terra-stories"
    assert settings.glm_writer_deployment == "glm-5.1"
    assert settings.glm_judge_deployment == "glm-5.2"


def test_get_settings_callable() -> None:
    assert get_settings() is not None


def test_normalize_azure_endpoint_strips_path_and_query() -> None:
    raw = (
        "https://agents-patterns-lab-oai.openai.azure.com/openai/deployments/x"
        "?api-version=2024-12-01-preview"
    )
    assert normalize_azure_endpoint(raw) == "https://agents-patterns-lab-oai.openai.azure.com/"


def test_settings_strips_whitespace_and_normalizes_endpoint() -> None:
    settings = Settings(
        _env_file=None,
        azure_openai_endpoint=("https://agents-patterns-lab-oai.openai.azure.com/openai/v1?x=1"),
        azure_openai_writer_deployment=" gpt-5.6-luna-stories \n",
    )
    assert settings.azure_openai_endpoint == ("https://agents-patterns-lab-oai.openai.azure.com/")
    assert settings.azure_openai_writer_deployment == "gpt-5.6-luna-stories"
