import pytest

from llm_text_intel.errors import LLMPermanentError, LLMTransientError
from llm_text_intel.llm.client import LLMClient
from llm_text_intel.schemas import LLMResponse
from tests.unit.fakes import FakeLLMClient


def _response(text: str = "ok") -> LLMResponse:
    return LLMResponse(text=text, input_tokens=1, output_tokens=1, model="fake-model")


class TestFakeLLMClientConformsToProtocol:
    def test_is_an_llm_client(self) -> None:
        client: LLMClient = FakeLLMClient(script=[_response()])
        assert isinstance(client, LLMClient)


class TestFakeLLMClientBehavior:
    def test_returns_scripted_response(self) -> None:
        client = FakeLLMClient(script=[_response("hello")])
        result = client.complete("prompt", max_tokens=100)
        assert result.text == "hello"

    def test_returns_responses_in_order(self) -> None:
        client = FakeLLMClient(script=[_response("first"), _response("second")])
        first = client.complete("p1", max_tokens=10)
        second = client.complete("p2", max_tokens=10)
        assert first.text == "first"
        assert second.text == "second"

    def test_raises_scripted_transient_error(self) -> None:
        client = FakeLLMClient(script=[LLMTransientError("rate limited")])
        with pytest.raises(LLMTransientError):
            client.complete("prompt", max_tokens=10)

    def test_raises_scripted_permanent_error(self) -> None:
        client = FakeLLMClient(script=[LLMPermanentError("bad request")])
        with pytest.raises(LLMPermanentError):
            client.complete("prompt", max_tokens=10)

    def test_records_prompts_passed_in(self) -> None:
        client = FakeLLMClient(script=[_response(), _response()])
        client.complete("first prompt", max_tokens=10)
        client.complete("second prompt", max_tokens=10)
        assert client.calls == ["first prompt", "second prompt"]

    def test_calling_beyond_script_raises_assertion_error(self) -> None:
        client = FakeLLMClient(script=[_response()])
        client.complete("prompt", max_tokens=10)
        with pytest.raises(AssertionError):
            client.complete("prompt", max_tokens=10)
