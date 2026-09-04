# Phase 3 — Groq LLM Client

**Status:** Completed

## Objective

Implement a real `GroqClient` behind the existing `LLMClient` protocol,
using the official Groq Python SDK, with provider-specific code fully
isolated inside the client module.

This phase was originally planned around Anthropic; the provider was
changed to Groq before implementation began, which is why Phase 1's
config field and Phase 0/2's Anthropic-flavored wording were updated here
rather than in their original phases.

## Implemented work

- `src/llm_text_intel/llm/groq_client.py`: `GroqClient`, the only module
  permitted to import the `groq` SDK.
- `src/llm_text_intel/config.py`: `anthropic_api_key` -> `groq_api_key`;
  `model_name` default -> `llama-3.3-70b-versatile`.
- `.env.example`: `ANTHROPIC_API_KEY` -> `GROQ_API_KEY`.
- Stale "Anthropic" wording in `README.md`, `docs/adr/0002-...`, and
  `llm/client.py` updated to "Groq".
- `tests/unit/test_config.py` updated for the renamed field/env var.
- `tests/unit/test_groq_client.py`: success-path and error-mapping tests,
  mocking the Groq SDK boundary directly (no network calls).

## Design decisions

- **Model:** `llama-3.3-70b-versatile`, confirmed via Groq's official model
  documentation as a current production model with a 131K context window,
  suited to summarization/extraction tasks. Fully overridable via
  `MODEL_NAME`.
- **Error mapping** (`groq.*` -> `llm_text_intel.errors.*`):
  - Transient: `APIConnectionError`, `APITimeoutError`, `RateLimitError`,
    `InternalServerError` (5xx).
  - Permanent: everything else caught by the generic `APIStatusError`
    (`AuthenticationError`, `BadRequestError`, `NotFoundError`,
    `PermissionDeniedError`, `ConflictError`, `UnprocessableEntityError`;
    all 4xx-class).
  - `except` clauses ordered specific-before-generic since several
    transient types subclass `APIStatusError`.
- No `anthropic` dependency was ever added to the project.

## Tests / validation

10 new tests (36 total at the time). Groq SDK calls mocked directly on the
client instance (`MagicMock` on `chat.completions.create`); error tests
construct real `groq.*Error` instances using minimal `httpx.Request`/
`httpx.Response` objects to verify against the SDK's actual exception
shapes. `pytest` and `ruff check .` passed; an `isinstance(client,
LLMClient)` sanity check confirmed protocol conformance.

## Dependencies introduced

`groq>=1.7`.

## Known risks / deferred items

- Model availability/pricing on Groq is an external fact, not pinned
  beyond the model-id string; acceptable since it is env-overridable.
- Response parsing assumes Groq's OpenAI-compatible response shape holds.
- No real (network) integration test exists yet; deferred as an
  explicitly opt-in addition if needed later.
