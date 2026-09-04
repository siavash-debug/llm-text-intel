"""Test doubles for llm_text_intel.llm.client.LLMClient.

Kept in tests/, not in the package: these are test-only fixtures, not part
of the application's public surface.
"""

from collections import deque
from collections.abc import Sequence

from llm_text_intel.errors import LLMPermanentError, LLMTransientError
from llm_text_intel.schemas import LLMResponse


class FakeLLMClient:
    """An LLMClient that returns pre-scripted responses/errors in order.

    Each entry in ``script`` is either an ``LLMResponse`` to return, or an
    exception instance to raise. Calling ``complete`` beyond the end of the
    script raises ``AssertionError`` to catch unexpected extra calls in tests.
    """

    def __init__(self, script: Sequence[LLMResponse | Exception]) -> None:
        self._script: deque[LLMResponse | Exception] = deque(script)
        self.calls: list[str] = []

    def complete(self, prompt: str, *, max_tokens: int) -> LLMResponse:
        self.calls.append(prompt)
        if not self._script:
            raise AssertionError("FakeLLMClient.complete called more times than scripted")
        outcome = self._script.popleft()
        if isinstance(outcome, LLMTransientError | LLMPermanentError):
            raise outcome
        return outcome
