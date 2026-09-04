from pathlib import Path

import pytest

from llm_text_intel.config import Settings, load_settings
from llm_text_intel.errors import ConfigurationError


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests are isolated from the developer's real .env/environment."""
    for key in ("GROQ_API_KEY", "MODEL_NAME", "MAX_RETRIES"):
        monkeypatch.delenv(key, raising=False)


def _settings(**overrides: object) -> Settings:
    # _env_file=None prevents pydantic-settings from reading a real .env file
    # during tests, keeping them hermetic regardless of the developer's setup.
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


class TestSettings:
    def test_loads_with_required_value(self) -> None:
        settings = _settings(groq_api_key="gsk-test")
        assert settings.groq_api_key == "gsk-test"

    def test_defaults_are_applied(self) -> None:
        settings = _settings(groq_api_key="gsk-test")
        assert settings.model_name == "llama-3.3-70b-versatile"
        assert settings.max_retries == 2
        assert settings.max_input_chars == 20_000
        assert settings.max_output_tokens == 1024

    def test_missing_api_key_raises_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # load_settings() reads ".env" relative to the cwd. Run from a
        # directory with no .env so this test is independent of whether the
        # developer has a real .env in the project root.
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ConfigurationError):
            load_settings()

    def test_empty_api_key_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
            _settings(groq_api_key="")

    def test_negative_max_retries_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError
            _settings(groq_api_key="gsk-test", max_retries=-1)

    def test_zero_max_retries_allowed(self) -> None:
        settings = _settings(groq_api_key="gsk-test", max_retries=0)
        assert settings.max_retries == 0

    def test_env_var_overrides_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "gsk-from-env")
        monkeypatch.setenv("MODEL_NAME", "llama-3.1-8b-instant")
        settings = _settings()
        assert settings.groq_api_key == "gsk-from-env"
        assert settings.model_name == "llama-3.1-8b-instant"
