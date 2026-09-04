# Phase 1 — Configuration & Domain Schemas

**Status:** Completed

## Objective

Define the application's environment-based configuration and its core data
contracts (`TextAnalysis`, `LLMResponse`), plus the minimal error taxonomy
they need — pure, unit-testable, no network/LLM/CLI code.

## Implemented work

- `src/llm_text_intel/errors.py`: `AnalysisError` (base), `ConfigurationError`.
- `src/llm_text_intel/schemas.py`: `TextAnalysis` (title/summary/keywords,
  frozen, with length/count constraints), `LLMResponse` (text, token
  counts, model — frozen).
- `src/llm_text_intel/config.py`: `Settings` (`pydantic-settings`
  `BaseSettings`, env + `.env` loading) and `load_settings()`, which wraps
  `pydantic.ValidationError` in `ConfigurationError`.
- `tests/unit/test_schemas.py`, `tests/unit/test_config.py`.

Note: the original API key field/default were later renamed from
Anthropic-specific values to Groq-specific values in Phase 3 (see
[phase-3.md](phase-3.md)). `Settings` also gained two cost-estimation
fields in Phase 7 (`input_cost_per_million_tokens`,
`output_cost_per_million_tokens`) not described below — this doc reflects
the scope of Phase 1 itself, not the current full state of `config.py`.

## Design decisions

- Config validation happens eagerly (`load_settings()` fails fast on
  missing required values) rather than failing later at first LLM call.
- `TextAnalysis`/`LLMResponse` are `frozen=True` — immutable contracts.
- Only `ConfigurationError` was added at this phase; `LLMTransientError`/
  `LLMPermanentError` were deferred to Phase 2, where they were actually
  needed.

## Tests / validation

19 unit tests covering valid construction, invalid/missing/oversized
fields, immutability, boundary values, env var overrides, and missing
required config raising `ConfigurationError`. `pytest`, `ruff check .`,
and an import check all passed.

## Dependencies introduced

`pydantic>=2.6`, `pydantic-settings>=2.2`.

## Known risks / deferred items

Schema constraint values (keyword count, length bounds) were provisional
at the time, pending observation of real LLM output in later phases.
