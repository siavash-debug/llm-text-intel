import pytest

from llm_text_intel.config import Settings, load_settings
from llm_text_intel.errors import ConfigurationError


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests are isolated from the developer's real .env/environment."""
    for key in ("ANTHROPIC_API_KEY", "MODEL_NAME", "MAX_RETRIES"):
        monkeypatch.delenv(key, raising=False)


def _settings(**overrides: object) -> Settings:
    # _env_file=None prevents pydantic-settings from reading a real .env file
    # during tests, keeping them hermetic regardless of the developer's setup.
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


class TestSettings:
    def test_loads_with_required_value(self) -> None:
        settings = _settings(anthropic_api_key="sk-test")
        assert settings.anthropic_api_key == "sk-test"

    def test_defaults_are_applied(self) -> None:
        settings = _settings(anthropic_api_key="sk-test")
        assert settings.model_name == "claude-sonnet-5"
        assert settings.max_retries == 2
        assert settings.max_input_chars == 20_000
        assert settings.max_output_tokens == 1024

    def test_missing_api_key_raises_configuration_error(self) -> None:
        # No .env file is committed to the repo and _clean_env stripped the
        # relevant environment variables, so this is missing by construction.
        with pytest.raises(ConfigurationError):
            load_settings()

    def test_empty_api_key_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
            _settings(anthropic_api_key="")

    def test_negative_max_retries_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
            _settings(anthropic_api_key="sk-test", max_retries=-1)

    def test_zero_max_retries_allowed(self) -> None:
        settings = _settings(anthropic_api_key="sk-test", max_retries=0)
        assert settings.max_retries == 0

    def test_env_var_overrides_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
        monkeypatch.setenv("MODEL_NAME", "claude-haiku-4-5")
        settings = _settings()
        assert settings.anthropic_api_key == "sk-from-env"
        assert settings.model_name == "claude-haiku-4-5"
