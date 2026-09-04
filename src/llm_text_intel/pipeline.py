"""Core orchestration: text in, validated TextAnalysis out.

This is the application's one public entry point (``analyze``). Interfaces
(CLI now, a possible FastAPI wrapper later) call only this function; no
interface-specific concerns belong here, and no provider-specific types
appear here — only ``LLMClient``.

LLM output is treated as untrusted input: the raw response text is neither
valid JSON nor schema-conformant until proven so, and retries are bounded so
a persistently misbehaving model or provider cannot cause an unbounded loop.
"""

import json

from pydantic import ValidationError

from llm_text_intel.config import Settings
from llm_text_intel.errors import InvalidInputError, InvalidOutputError, LLMTransientError
from llm_text_intel.llm.client import LLMClient
from llm_text_intel.prompts.analyze import build_analyze_prompt
from llm_text_intel.schemas import TextAnalysis


def analyze(text: str, client: LLMClient, settings: Settings) -> TextAnalysis:
    """Analyze ``text`` into a title, summary, and keywords.

    Raises:
        llm_text_intel.errors.InvalidInputError: ``text`` fails input
            validation. The LLM is never called in this case.
        llm_text_intel.errors.InvalidOutputError: the LLM's output could not
            be parsed as valid ``TextAnalysis`` JSON after all retries.
        llm_text_intel.errors.LLMTransientError: the provider kept failing
            transiently after all retries.
        llm_text_intel.errors.LLMPermanentError: the provider failed in a
            non-retryable way. Not caught here; propagates immediately.
    """
    _validate_input(text, settings)

    prompt = build_analyze_prompt(text)
    last_error: Exception | None = None

    for _ in range(settings.max_retries + 1):
        try:
            response = client.complete(prompt, max_tokens=settings.max_output_tokens)
        except LLMTransientError as exc:
            last_error = exc
            continue

        try:
            data = json.loads(response.text)
            return TextAnalysis.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            prompt = _build_correction_prompt(text, response.text, exc)

    if isinstance(last_error, LLMTransientError):
        raise last_error
    raise InvalidOutputError(
        f"LLM output failed validation after {settings.max_retries} retries: {last_error}"
    ) from last_error


def _validate_input(text: str, settings: Settings) -> None:
    if not text.strip():
        raise InvalidInputError("Input text must not be empty.")
    if len(text) > settings.max_input_chars:
        raise InvalidInputError(
            f"Input text exceeds max_input_chars ({settings.max_input_chars})."
        )


def _build_correction_prompt(text: str, previous_output: str, error: Exception) -> str:
    base = build_analyze_prompt(text)
    return (
        f"{base}\n\n"
        f"Your previous response was invalid: {error}\n"
        f"Previous response: {previous_output}\n"
        "Respond again with ONLY a valid JSON object matching the required fields."
    )
