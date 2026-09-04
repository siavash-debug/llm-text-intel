import json

import pytest

from llm_text_intel.config import Settings
from llm_text_intel.interfaces.cli import main
from llm_text_intel.schemas import LLMResponse
from tests.unit.fakes import FakeLLMClient

VALID_JSON = '{"title": "A Title", "summary": "A summary.", "keywords": ["a", "b"]}'


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, groq_api_key="gsk-test", **overrides)  # type: ignore[call-arg]


def _response(text: str) -> LLMResponse:
    return LLMResponse(text=text, input_tokens=1, output_tokens=1, model="fake-model")


class TestCliSuccess:
    def test_prints_json_result_and_returns_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        exit_code = main(["some article text"], client=client, settings=_settings())

        assert exit_code == 0
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert payload["title"] == "A Title"
        assert payload["summary"] == "A summary."
        assert payload["keywords"] == ["a", "b"]

    def test_reads_text_from_stdin_when_no_argument_given(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO("piped in text"))
        client = FakeLLMClient(script=[_response(VALID_JSON)])
        exit_code = main([], client=client, settings=_settings())

        assert exit_code == 0
        assert client.calls[0].count("piped in text") == 1


class TestCliInputErrors:
    def test_empty_text_reports_error_without_calling_client(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        client = FakeLLMClient(script=[])
        exit_code = main([""], client=client, settings=_settings())

        assert exit_code == 1
        assert client.calls == []
        err = capsys.readouterr().err
        assert err.startswith("Error:")


class TestCliPipelineErrors:
    def test_invalid_output_after_retries_reports_error_and_returns_one(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        client = FakeLLMClient(script=[_response("not json"), _response("still not json")])
        exit_code = main(["text"], client=client, settings=_settings(max_retries=1))

        assert exit_code == 1
        err = capsys.readouterr().err
        assert err.startswith("Error:")
        # No raw exception type/traceback leaked to the user.
        assert "Traceback" not in err

    def test_missing_configuration_reports_error_and_returns_one(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: object, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.chdir(tmp_path)  # type: ignore[arg-type]
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        exit_code = main(["some text"])

        assert exit_code == 1
        err = capsys.readouterr().err
        assert err.startswith("Error:")
