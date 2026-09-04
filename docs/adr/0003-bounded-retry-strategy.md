# 0003. Bounded retries with a single budget, distinguished by final error type

## Status

Accepted (implemented in Phase 5, `src/llm_text_intel/pipeline.py`)

## Context

`pipeline.analyze()` can fail in two structurally different ways: the
provider call itself fails transiently (rate limit, timeout, 5xx — see
`LLMTransientError`), or the provider responds successfully but the content
is not valid JSON / does not satisfy `TextAnalysis` (LLM output is treated
as untrusted input). Both are worth retrying; neither should retry forever.

A design with two independent retry budgets (one for transient provider
failures, one for invalid-output corrections) was considered, since it
would allow tuning each failure mode separately and logging a distinct
"retry reason" per attempt.

## Decision

Use a single retry budget: `settings.max_retries` bounds the *total* number
of extra attempts across both failure modes (`max_retries + 1` attempts in
total). On a transient error, the same prompt is retried. On invalid
output, the prompt is rebuilt with a correction message describing what was
wrong before retrying. `LLMPermanentError` is never retried — it propagates
on first occurrence.

The two failure modes remain distinguishable after the fact: the exception
type raised once the budget is exhausted is `LLMTransientError` if the last
failure was transient, or `InvalidOutputError` if it was a content
validation failure.

## Consequences

- Simpler to implement, test, and reason about than two independent
  counters — one loop, one bound, checked by `tests/unit/test_pipeline.py`
  (`test_retry_count_never_exceeds_max_retries`).
- Per-attempt failure *reason* is not separately logged inside the retry
  loop itself; `observability.analyze_with_observability` (Phase 7) logs
  the aggregate `retry_count` and the final `outcome`/`error_type` per
  request, which is sufficient for the diagnostics this project needs today.
- If per-attempt-reason logging or independently tunable budgets become a
  real requirement, that would warrant revisiting this decision — no such
  requirement exists today.
- No retry backoff/delay is implemented; retries are immediate. This is a
  known, accepted limitation for the MVP (see the Phase 5 report), not
  something this ADR claims to solve.
