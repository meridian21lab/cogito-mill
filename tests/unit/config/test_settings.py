from cogito_mill.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.hf_dataset_namespace == "ksopyla"
    assert settings.glm_model == "glm-4.5"


def test_get_settings_callable() -> None:
    assert get_settings() is not None
