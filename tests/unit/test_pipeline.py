import pytest

from llm_text_intel.config import Settings
from llm_text_intel.errors import (
    InvalidInputError,
    InvalidOutputError,
    LLMPermanentError,
    LLMTransientError,
)
from llm_text_intel.pipeline import analyze
from llm_text_intel.schemas import LLMResponse
from tests.unit.fakes import FakeLLMClient

VALID_JSON = '{"title": "A Title", "summary": "A summary.", "keywords": ["a", "b"]}'


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, groq_api_key="gsk-test", **overrides)  # type: ignore[call-arg]


def _response(text: str) -> LLMResponse:
    return LLMResponse(text=text, input_tokens=1, output_tokens=1, model="fake-model")


class TestAnalyzeHappyPath:
    def test_valid_json_first_try_returns_text_analysis(self) -> None:
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        result = analyze("some article text", client=client, settings=_settings())

        assert result.title == "A Title"
        assert result.summary == "A summary."
        assert result.keywords == ["a", "b"]
        assert len(client.calls) == 1


class TestAnalyzeInputValidation:
    def test_empty_text_raises_invalid_input_error_without_calling_client(self) -> None:
        client = FakeLLMClient(script=[])
        with pytest.raises(InvalidInputError):
            analyze("", client=client, settings=_settings())
        assert client.calls == []

    def test_whitespace_only_text_raises_invalid_input_error(self) -> None:
        client = FakeLLMClient(script=[])
        with pytest.raises(InvalidInputError):
            analyze("   \n  ", client=client, settings=_settings())
        assert client.calls == []

    def test_oversized_text_raises_invalid_input_error_without_calling_client(self) -> None:
        client = FakeLLMClient(script=[])
        settings = _settings(max_input_chars=10)
        with pytest.raises(InvalidInputError):
            analyze("x" * 11, client=client, settings=settings)
        assert client.calls == []


class TestAnalyzeMalformedOutputRetry:
    def test_malformed_json_retried_then_succeeds(self) -> None:
        client = FakeLLMClient(script=[_response("not json"), _response(VALID_JSON)])
        result = analyze("text", client=client, settings=_settings(max_retries=2))

        assert result.title == "A Title"
        assert len(client.calls) == 2

    def test_schema_violation_retried_then_succeeds(self) -> None:
        invalid_schema = '{"title": "", "summary": "s", "keywords": ["a"]}'
        client = FakeLLMClient(script=[_response(invalid_schema), _response(VALID_JSON)])
        result = analyze("text", client=client, settings=_settings(max_retries=2))

        assert result.title == "A Title"
        assert len(client.calls) == 2

    def test_persistent_malformed_output_exhausts_retries(self) -> None:
        client = FakeLLMClient(script=[_response("not json"), _response("still not json")])
        with pytest.raises(InvalidOutputError):
            analyze("text", client=client, settings=_settings(max_retries=1))

        # max_retries=1 => at most 2 total attempts, never more.
        assert len(client.calls) == 2

    def test_correction_retry_includes_previous_error_context(self) -> None:
        client = FakeLLMClient(script=[_response("not json"), _response(VALID_JSON)])
        analyze("text", client=client, settings=_settings(max_retries=2))

        assert "invalid" in client.calls[1].lower()


class TestAnalyzeTransientErrorRetry:
    def test_transient_error_retried_then_succeeds(self) -> None:
        client = FakeLLMClient(script=[LLMTransientError("rate limited"), _response(VALID_JSON)])
        result = analyze("text", client=client, settings=_settings(max_retries=2))

        assert result.title == "A Title"
        assert len(client.calls) == 2

    def test_persistent_transient_error_exhausts_retries_and_raises(self) -> None:
        client = FakeLLMClient(
            script=[LLMTransientError("e1"), LLMTransientError("e2")]
        )
        with pytest.raises(LLMTransientError):
            analyze("text", client=client, settings=_settings(max_retries=1))

        assert len(client.calls) == 2


class TestAnalyzePermanentErrorPropagation:
    def test_permanent_error_propagates_immediately_without_retry(self) -> None:
        client = FakeLLMClient(script=[LLMPermanentError("bad api key")])
        with pytest.raises(LLMPermanentError):
            analyze("text", client=client, settings=_settings(max_retries=3))

        assert len(client.calls) == 1


class TestAnalyzeRetryBound:
    def test_retry_count_never_exceeds_max_retries(self) -> None:
        max_retries = 2
        client = FakeLLMClient(
            script=[_response("not json")] * (max_retries + 1)
        )
        with pytest.raises(InvalidOutputError):
            analyze("text", client=client, settings=_settings(max_retries=max_retries))

        assert len(client.calls) == max_retries + 1

    def test_zero_max_retries_allows_exactly_one_attempt(self) -> None:
        client = FakeLLMClient(script=[_response("not json")])
        with pytest.raises(InvalidOutputError):
            analyze("text", client=client, settings=_settings(max_retries=0))

        assert len(client.calls) == 1
