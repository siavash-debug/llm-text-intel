"""Error taxonomy for llm_text_intel.

Kept minimal and explicit: only the types genuinely needed by the current
phase exist here. Later phases (LLM client, pipeline) will add more specific
subclasses as they need to distinguish new failure modes (e.g. transient vs.
permanent provider errors, invalid LLM output).
"""


class AnalysisError(Exception):
    """Base class for all application-level errors in this package."""


class ConfigurationError(AnalysisError):
    """Required configuration is missing or invalid."""


class LLMTransientError(AnalysisError):
    """A provider call failed in a way that may succeed if retried.

    E.g. rate limiting, timeouts, 5xx server errors.
    """


class LLMPermanentError(AnalysisError):
    """A provider call failed in a way that will not succeed if retried.

    E.g. authentication failure, invalid request.
    """


class InvalidInputError(AnalysisError):
    """The text given to analyze() does not satisfy input constraints."""


class InvalidOutputError(AnalysisError):
    """The LLM's output did not satisfy the output contract after retries.

    LLM output is treated as untrusted input: this is a normal, expected
    failure mode, not just a defensive edge case.
    """
