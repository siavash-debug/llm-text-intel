import json

import pytest

from llm_text_intel.config import Settings
from llm_text_intel.errors import InvalidOutputError
from llm_text_intel.observability import analyze_with_observability
from llm_text_intel.schemas import LLMResponse
from tests.unit.fakes import FakeLLMClient

VALID_JSON = '{"title": "A Title", "summary": "A summary.", "keywords": ["a", "b"]}'


def _settings(**overrides: object) -> Settings:
    overrides.setdefault("groq_api_key", "gsk-test")
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def _response(text: str, input_tokens: int = 10, output_tokens: int = 5) -> LLMResponse:
    return LLMResponse(
        text=text, input_tokens=input_tokens, output_tokens=output_tokens, model="fake-model"
    )


def _log_records(caplog: pytest.LogCaptureFixture) -> list[dict]:
    return [json.loads(r.message) for r in caplog.records]


class TestAnalyzeWithObservabilitySuccess:
    def test_returns_same_result_as_pipeline(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        result = analyze_with_observability("some text", client=client, settings=_settings())

        assert result.title == "A Title"

    def test_logs_exactly_one_record_on_success(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        analyze_with_observability("some text", client=client, settings=_settings())

        records = _log_records(caplog)
        assert len(records) == 1
        assert records[0]["outcome"] == "success"
        assert records[0]["error_type"] is None

    def test_logged_record_has_expected_fields(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response(VALID_JSON, input_tokens=100, output_tokens=50)])
        analyze_with_observability("hello world", client=client, settings=_settings())

        record = _log_records(caplog)[0]
        assert record["model"] == "fake-model"
        assert record["input_length"] == len("hello world")
        assert record["input_tokens"] == 100
        assert record["output_tokens"] == 50
        assert record["retry_count"] == 0
        assert isinstance(record["latency_ms"], int | float)
        assert record["latency_ms"] >= 0

    def test_estimated_cost_is_computed_from_configured_rates(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(
            script=[_response(VALID_JSON, input_tokens=1_000_000, output_tokens=1_000_000)]
        )
        settings = _settings(input_cost_per_million_tokens=1.0, output_cost_per_million_tokens=2.0)
        analyze_with_observability("text", client=client, settings=settings)

        record = _log_records(caplog)[0]
        assert record["estimated_cost_usd"] == pytest.approx(3.0)

    def test_retry_count_reflects_extra_attempts(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response("not json"), _response(VALID_JSON)])
        analyze_with_observability("text", client=client, settings=_settings(max_retries=2))

        record = _log_records(caplog)[0]
        assert record["retry_count"] == 1

    def test_raw_input_text_is_not_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        secret_text = "super secret user content, do not log me"
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        analyze_with_observability(secret_text, client=client, settings=_settings())

        for record in caplog.records:
            assert secret_text not in record.message

    def test_llm_response_text_is_not_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        analyze_with_observability("text", client=client, settings=_settings())

        for record in caplog.records:
            assert VALID_JSON not in record.message

    def test_api_key_is_not_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        settings = _settings(groq_api_key="gsk-super-secret-value")
        analyze_with_observability("text", client=client, settings=settings)

        for record in caplog.records:
            assert "gsk-super-secret-value" not in record.message


class TestAnalyzeWithObservabilityFailure:
    def test_logs_failure_outcome_and_reraises(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[_response("not json"), _response("still not json")])

        with pytest.raises(InvalidOutputError):
            analyze_with_observability("text", client=client, settings=_settings(max_retries=1))

        record = _log_records(caplog)[0]
        assert record["outcome"] == "failure"
        assert record["error_type"] == "InvalidOutputError"
        assert record["retry_count"] == 1

    def test_input_validation_failure_still_logs_one_record(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level("INFO", logger="llm_text_intel.observability")
        client = FakeLLMClient(script=[])

        with pytest.raises(Exception):  # noqa: B017 - InvalidInputError, re-raised
            analyze_with_observability("", client=client, settings=_settings())

        records = _log_records(caplog)
        assert len(records) == 1
        assert records[0]["outcome"] == "failure"
        assert records[0]["retry_count"] == 0
        assert records[0]["input_tokens"] == 0
