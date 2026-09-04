"""Edge-case coverage for input handling across schemas and the pipeline.

These fill gaps not exercised by the phase-by-phase happy-path/error-path
tests: unicode/emoji content, minimal valid input, control characters, and
exact input-length boundaries. No network calls.
"""

import pytest

from llm_text_intel.config import Settings
from llm_text_intel.errors import InvalidInputError
from llm_text_intel.pipeline import analyze
from llm_text_intel.schemas import LLMResponse, TextAnalysis
from tests.unit.fakes import FakeLLMClient


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, groq_api_key="gsk-test", **overrides)  # type: ignore[call-arg]


def _response(text: str) -> LLMResponse:
    return LLMResponse(text=text, input_tokens=1, output_tokens=1, model="fake-model")


class TestSchemaUnicodeAndEmoji:
    def test_text_analysis_accepts_emoji_and_unicode(self) -> None:
        analysis = TextAnalysis(
            title="Café Culture in Paris \U0001f950",
            summary="A short piece about cafés, éclairs, and \U0001f378 nightlife.",
            keywords=["café", "éclair", "\U0001f378", "Paris"],
        )
        assert "\U0001f950" in analysis.title
        assert "\U0001f378" in analysis.keywords


class TestPipelineMinimalInput:
    def test_single_character_input_is_accepted_and_calls_client(self) -> None:
        valid_json = '{"title": "T", "summary": "S", "keywords": ["k"]}'
        client = FakeLLMClient(script=[_response(valid_json)])
        result = analyze("x", client=client, settings=_settings())

        assert result.title == "T"
        assert len(client.calls) == 1


class TestPipelineUnicodeInput:
    def test_unicode_and_emoji_input_flows_through_to_the_client(self) -> None:
        valid_json = '{"title": "T", "summary": "S", "keywords": ["k"]}'
        client = FakeLLMClient(script=[_response(valid_json)])
        text = "Über cafés and \U0001f680 rockets — a story."

        result = analyze(text, client=client, settings=_settings())

        assert result.title == "T"
        assert text in client.calls[0]

    def test_unicode_response_keywords_are_parsed_correctly(self) -> None:
        valid_json = '{"title": "Têtre", "summary": "S", "keywords": ["日本語", "café"]}'
        client = FakeLLMClient(script=[_response(valid_json)])

        result = analyze("some text", client=client, settings=_settings())

        assert result.title == "Têtre"
        assert "日本語" in result.keywords


class TestPipelineControlCharacters:
    def test_input_with_embedded_newlines_and_tabs_does_not_crash(self) -> None:
        valid_json = '{"title": "T", "summary": "S", "keywords": ["k"]}'
        client = FakeLLMClient(script=[_response(valid_json)])
        text = "Line one.\nLine two.\tTabbed.\r\nWindows newline."

        result = analyze(text, client=client, settings=_settings())

        assert result.title == "T"

    def test_input_with_null_byte_does_not_crash(self) -> None:
        valid_json = '{"title": "T", "summary": "S", "keywords": ["k"]}'
        client = FakeLLMClient(script=[_response(valid_json)])
        text = "before\x00after"

        result = analyze(text, client=client, settings=_settings())

        assert result.title == "T"


class TestPipelineInputLengthBoundary:
    def test_input_exactly_at_max_input_chars_is_accepted(self) -> None:
        valid_json = '{"title": "T", "summary": "S", "keywords": ["k"]}'
        settings = _settings(max_input_chars=10)
        client = FakeLLMClient(script=[_response(valid_json)])

        result = analyze("x" * 10, client=client, settings=settings)

        assert result.title == "T"
        assert len(client.calls) == 1

    def test_input_one_char_over_max_input_chars_is_rejected(self) -> None:
        settings = _settings(max_input_chars=10)
        client = FakeLLMClient(script=[])

        with pytest.raises(InvalidInputError):
            analyze("x" * 11, client=client, settings=settings)

        assert client.calls == []
