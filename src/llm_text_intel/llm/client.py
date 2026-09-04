"""Provider-agnostic LLM client interface.

Any concrete provider implementation (e.g. Groq) must translate its own
SDK-specific exceptions into ``LLMTransientError``/``LLMPermanentError`` at
this boundary — nothing upstream of a client implementation should ever see
a provider-specific exception type.
"""

from typing import Protocol, runtime_checkable

from llm_text_intel.schemas import LLMResponse


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, prompt: str, *, max_tokens: int) -> LLMResponse:
        """Send a prompt to the provider and return its raw response.

        Raises:
            llm_text_intel.errors.LLMTransientError: on a retryable failure.
            llm_text_intel.errors.LLMPermanentError: on a non-retryable failure.
        """
        ...
