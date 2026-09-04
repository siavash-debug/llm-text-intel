"""Environment-based application configuration.

Settings are loaded from environment variables (optionally via a local
``.env`` file, never committed — see ``.env.example``). Required values with
no safe default (currently just the API key) raise ``ConfigurationError``
eagerly when missing, rather than failing later at first LLM call.
"""

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from llm_text_intel.errors import ConfigurationError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    groq_api_key: str = Field(min_length=1)
    model_name: str = "llama-3.3-70b-versatile"
    max_retries: int = Field(default=2, ge=0)
    max_input_chars: int = Field(default=20_000, gt=0)
    max_output_tokens: int = Field(default=1024, gt=0)

    # Approximate on-demand pricing for the default model (USD per 1M
    # tokens), used only to estimate request cost in observability logs.
    # Provider pricing changes over time and by model; override via env if
    # it drifts, rather than treating these as authoritative.
    input_cost_per_million_tokens: float = Field(default=0.59, ge=0)
    output_cost_per_million_tokens: float = Field(default=0.79, ge=0)


def load_settings() -> Settings:
    """Load settings from the environment, raising a clear error if invalid."""
    try:
        return Settings()
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid or missing configuration: {exc}") from exc
