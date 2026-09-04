# Phase 2 — LLM Client Interface + Fake Implementation

**Status:** Completed

## Objective

Define the provider-agnostic `LLMClient` protocol and a `FakeLLMClient`
test double, so all downstream logic can be developed and tested without
any network dependency.

## Implemented work

- `src/llm_text_intel/errors.py`: added `LLMTransientError` (retryable) and
  `LLMPermanentError` (non-retryable).
- `src/llm_text_intel/llm/client.py`: `LLMClient`, a `@runtime_checkable`
  `typing.Protocol` with a single `complete(prompt, *, max_tokens) ->
  LLMResponse` method.
- `tests/unit/fakes.py`: `FakeLLMClient` — a scripted test double (returns
  responses or raises errors in order); kept in `tests/`, not shipped in
  the package.
- `tests/unit/test_llm_client.py`.

## Design decisions

- `LLMClient` is a structural `Protocol`, not an ABC — no inheritance
  required from any future concrete client.
- The interface's documented contract is that only `LLMTransientError`/
  `LLMPermanentError` ever escape `complete()` — no provider-specific
  exception should reach calling code.
- `FakeLLMClient` lives in `tests/unit/`, keeping test-only fixtures out of
  the shipped package's public surface.

## Tests / validation

7 new tests (26 total at the time): protocol conformance
(`isinstance`), scripted response return and ordering, scripted
transient/permanent error raising, call recording, and an
`AssertionError` guard against unexpected extra calls. `pytest` and
`ruff check .` passed.

## Dependencies introduced

None.

## Known risks / deferred items

None specific to this phase — the concrete mapping from a real provider
SDK's exceptions to `LLMTransientError`/`LLMPermanentError` was explicitly
left to the next phase (originally planned for Anthropic, actually
implemented for Groq — see [phase-3.md](phase-3.md)).
