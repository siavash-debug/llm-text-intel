"""Groq implementation of the LLMClient protocol.

This is the only module in the application allowed to import the ``groq``
SDK or depend on its types. Everything upstream depends on
``llm_text_intel.llm.client.LLMClient`` and
``llm_text_intel.schemas.LLMResponse`` only.
"""

import groq

from llm_text_intel.errors import LLMPermanentError, LLMTransientError
from llm_text_intel.schemas import LLMResponse


class GroqClient:
    """LLMClient implementation backed by the Groq chat completions API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = groq.Groq(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, *, max_tokens: int) -> LLMResponse:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
        except (groq.APIConnectionError, groq.APITimeoutError, groq.RateLimitError) as exc:
            raise LLMTransientError(str(exc)) from exc
        except groq.InternalServerError as exc:
            raise LLMTransientError(str(exc)) from exc
        except groq.APIStatusError as exc:
            # Any other non-2xx status (auth, bad request, not found, etc.)
            # is treated as non-retryable.
            raise LLMPermanentError(str(exc)) from exc

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            model=response.model,
        )
