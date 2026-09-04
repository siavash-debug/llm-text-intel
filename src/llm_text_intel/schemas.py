"""Domain/output contracts for llm_text_intel.

These models are the stable boundary between the rest of the application
and any LLM response. LLM output is untrusted input: nothing downstream may
assume a response is well-formed until it has been validated against
``TextAnalysis``.
"""

from pydantic import BaseModel, ConfigDict, Field


class LLMResponse(BaseModel):
    """A raw completion from an LLM provider, before any content validation.

    This only captures what any provider call returns (text + usage +
    model identity) — it says nothing about whether ``text`` is valid
    JSON or satisfies ``TextAnalysis``.
    """

    model_config = ConfigDict(frozen=True)

    text: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    model: str = Field(min_length=1)


class TextAnalysis(BaseModel):
    """The application's structured output contract for a piece of text."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=2000)
    keywords: list[str] = Field(min_length=1, max_length=15)
