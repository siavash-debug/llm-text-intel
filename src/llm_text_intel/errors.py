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
