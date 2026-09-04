"""Structured, per-request observability for the analyze pipeline.

``analyze_with_observability`` wraps ``pipeline.analyze`` unchanged — it
instruments the ``LLMClient`` passed in to count calls and accumulate token
usage, then emits exactly one structured log record per request, on both
success and failure.

Logs are intentionally minimal: model, input length, latency, token counts,
estimated cost, retry count, and outcome. Raw input text, prompts, and LLM
responses are never logged, so nothing here can leak user-submitted content
or provider output into log storage.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass

from llm_text_intel.config import Settings
from llm_text_intel.errors import AnalysisError
from llm_text_intel.llm.client import LLMClient
from llm_text_intel.pipeline import analyze
from llm_text_intel.schemas import LLMResponse, TextAnalysis

logger = logging.getLogger("llm_text_intel.observability")


@dataclass(frozen=True)
class RequestLog:
    model: str
    input_length: int
    latency_ms: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    retry_count: int
    outcome: str  # "success" or "failure"
    error_type: str | None = None


class _InstrumentedLLMClient:
    """Wraps an LLMClient to count calls and accumulate token usage.

    Internal to this module's instrumentation only — not part of the
    LLMClient surface used elsewhere in the application.
    """

    def __init__(self, wrapped: LLMClient) -> None:
        self._wrapped = wrapped
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.last_model: str | None = None

    def complete(self, prompt: str, *, max_tokens: int) -> LLMResponse:
        self.call_count += 1
        response = self._wrapped.complete(prompt, max_tokens=max_tokens)
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self.last_model = response.model
        return response


def analyze_with_observability(text: str, client: LLMClient, settings: Settings) -> TextAnalysis:
    """Call ``pipeline.analyze`` and log exactly one structured record.

    Behavior and exceptions are identical to ``pipeline.analyze`` — this
    only adds a logging side effect around it.
    """
    instrumented = _InstrumentedLLMClient(client)
    start = time.perf_counter()
    outcome = "success"
    error_type: str | None = None

    try:
        return analyze(text, client=instrumented, settings=settings)
    except AnalysisError as exc:
        outcome = "failure"
        error_type = type(exc).__name__
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        retry_count = max(instrumented.call_count - 1, 0)
        cost = _estimate_cost(
            instrumented.total_input_tokens, instrumented.total_output_tokens, settings
        )
        record = RequestLog(
            model=instrumented.last_model or settings.model_name,
            input_length=len(text),
            latency_ms=round(latency_ms, 2),
            input_tokens=instrumented.total_input_tokens,
            output_tokens=instrumented.total_output_tokens,
            estimated_cost_usd=round(cost, 6),
            retry_count=retry_count,
            outcome=outcome,
            error_type=error_type,
        )
        logger.info(json.dumps(asdict(record)))


def _estimate_cost(input_tokens: int, output_tokens: int, settings: Settings) -> float:
    input_cost = (input_tokens / 1_000_000) * settings.input_cost_per_million_tokens
    output_cost = (output_tokens / 1_000_000) * settings.output_cost_per_million_tokens
    return input_cost + output_cost
