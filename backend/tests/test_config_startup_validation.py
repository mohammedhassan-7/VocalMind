import warnings

import pytest

from app.core.config import Settings, validate_startup_settings


def _base_settings() -> Settings:
    return Settings(
        SECRET_KEY="test-secret-123",
        LLM_PROVIDER="groq",
        GROQ_API_KEY="groq-key",
        OLLAMA_CLOUD_API_KEY="",
    )


def test_validate_startup_settings_fails_on_default_secret_even_local():
    cfg = Settings(
        SECRET_KEY="CHANGE_THIS_TO_A_STRONG_SECRET_KEY_32B",
        IS_LOCAL=True,
        LLM_PROVIDER="groq",
        GROQ_API_KEY="groq-key",
    )
    with pytest.raises(RuntimeError, match="SECRET_KEY is still the default placeholder"):
        validate_startup_settings(cfg)


def test_validate_startup_settings_fails_when_groq_provider_missing_key():
    cfg = Settings(
        SECRET_KEY="test-secret-123",
        LLM_PROVIDER="groq",
        GROQ_API_KEY="",
    )
    with pytest.raises(RuntimeError, match="LLM_PROVIDER=groq requires GROQ_API_KEY"):
        validate_startup_settings(cfg)


def test_validate_startup_settings_fails_when_ollama_cloud_provider_missing_key():
    cfg = Settings(
        SECRET_KEY="test-secret-123",
        LLM_PROVIDER="ollama_cloud",
        OLLAMA_CLOUD_API_KEY="",
    )
    with pytest.raises(RuntimeError, match="LLM_PROVIDER=ollama_cloud requires OLLAMA_CLOUD_API_KEY"):
        validate_startup_settings(cfg)


def test_validate_startup_settings_warns_when_hf_token_missing():
    cfg = _base_settings()
    cfg.HF_TOKEN = ""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        validate_startup_settings(cfg)
    assert any("diarization is disabled" in str(item.message) for item in caught)


def test_validate_startup_settings_passes_when_all_required_values_set():
    cfg = Settings(
        SECRET_KEY="test-secret-123",
        LLM_PROVIDER="ollama_cloud",
        OLLAMA_CLOUD_API_KEY="ollama-key",
        HF_TOKEN="hf_abc123",
    )
    validate_startup_settings(cfg)
