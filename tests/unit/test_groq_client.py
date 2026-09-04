from types import SimpleNamespace
from unittest.mock import MagicMock

import groq
import httpx
import pytest

from llm_text_intel.errors import LLMPermanentError, LLMTransientError
from llm_text_intel.llm.groq_client import GroqClient


def _fake_chat_response(
    content: str = "hello",
    model: str = "llama-3.3-70b-versatile",
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        model=model,
    )


def _make_client(create_side_effect: object) -> GroqClient:
    """Build a GroqClient with its internal SDK client's create() mocked out.

    No real network/API calls are made: the groq.Groq instance's
    chat.completions.create method is replaced directly.
    """
    client = GroqClient(api_key="gsk-test", model="llama-3.3-70b-versatile")
    client._client.chat.completions.create = MagicMock(side_effect=create_side_effect)  # type: ignore[method-assign]
    return client


def _httpx_response(status_code: int) -> httpx.Response:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    return httpx.Response(status_code=status_code, request=request)


class TestGroqClientSuccess:
    def test_returns_llm_response_on_success(self) -> None:
        fake_response = _fake_chat_response(
            content="a summary", prompt_tokens=20, completion_tokens=8
        )
        client = _make_client(create_side_effect=[fake_response])

        result = client.complete("prompt text", max_tokens=100)

        assert result.text == "a summary"
        assert result.input_tokens == 20
        assert result.output_tokens == 8
        assert result.model == "llama-3.3-70b-versatile"

    def test_missing_usage_defaults_to_zero_tokens(self) -> None:
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="x"))],
            usage=None,
            model="llama-3.3-70b-versatile",
        )
        client = _make_client(create_side_effect=[fake_response])

        result = client.complete("prompt", max_tokens=10)

        assert result.input_tokens == 0
        assert result.output_tokens == 0

    def test_none_content_becomes_empty_string(self) -> None:
        fake_response = _fake_chat_response(content=None)  # type: ignore[arg-type]
        client = _make_client(create_side_effect=[fake_response])

        result = client.complete("prompt", max_tokens=10)

        assert result.text == ""


class TestGroqClientErrorMapping:
    def test_connection_error_is_transient(self) -> None:
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        client = _make_client(create_side_effect=groq.APIConnectionError(request=request))

        with pytest.raises(LLMTransientError):
            client.complete("prompt", max_tokens=10)

    def test_timeout_error_is_transient(self) -> None:
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        client = _make_client(create_side_effect=groq.APITimeoutError(request=request))

        with pytest.raises(LLMTransientError):
            client.complete("prompt", max_tokens=10)

    def test_rate_limit_error_is_transient(self) -> None:
        response = _httpx_response(429)
        client = _make_client(
            create_side_effect=groq.RateLimitError("rate limited", response=response, body=None)
        )

        with pytest.raises(LLMTransientError):
            client.complete("prompt", max_tokens=10)

    def test_internal_server_error_is_transient(self) -> None:
        response = _httpx_response(500)
        client = _make_client(
            create_side_effect=groq.InternalServerError(
                "server error", response=response, body=None
            )
        )

        with pytest.raises(LLMTransientError):
            client.complete("prompt", max_tokens=10)

    def test_authentication_error_is_permanent(self) -> None:
        response = _httpx_response(401)
        client = _make_client(
            create_side_effect=groq.AuthenticationError("bad key", response=response, body=None)
        )

        with pytest.raises(LLMPermanentError):
            client.complete("prompt", max_tokens=10)

    def test_bad_request_error_is_permanent(self) -> None:
        response = _httpx_response(400)
        client = _make_client(
            create_side_effect=groq.BadRequestError("bad request", response=response, body=None)
        )

        with pytest.raises(LLMPermanentError):
            client.complete("prompt", max_tokens=10)

    def test_not_found_error_is_permanent(self) -> None:
        response = _httpx_response(404)
        client = _make_client(
            create_side_effect=groq.NotFoundError("not found", response=response, body=None)
        )

        with pytest.raises(LLMPermanentError):
            client.complete("prompt", max_tokens=10)
