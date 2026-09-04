# 0004. Rule-based golden-set evaluation, opt-in against the real provider

## Status

Accepted (implemented in Phase 8, `tests/eval/`, `eval_data/golden_set.jsonl`)

## Context

The project's learning goals explicitly include LLM evaluation and prompt
regression testing. An LLM-as-judge approach (using a second LLM call to
score output quality) was considered, since it can assess more subjective
qualities (relevance, faithfulness) than rule-based checks can.

## Decision

Start with rule-based scoring only (`tests/eval/scoring.py`): each golden
example carries static, deterministic expectations (keyword-count bounds,
title/summary word-count bounds), and `score_example()` checks a produced
`TextAnalysis` against them with no LLM call involved. This part is free
and deterministic (`tests/eval/test_scoring.py`); it lives outside
`tests/unit/` since it evaluates the eval harness itself, not application
code, but is run alongside the unit suite as a matter of practice
(`pytest tests/unit tests/eval/test_scoring.py` — see README's Testing
section), not automatically picked up by `pytest tests/unit` alone.

The end-to-end check that actually calls the real Groq API
(`tests/eval/test_eval_suite.py::test_golden_set_pass_rate_meets_threshold`)
is:

- marked with a registered `eval` pytest marker,
- excluded from the default `pytest tests/unit` run,
- skipped automatically when no real `GROQ_API_KEY` is present,
- tied to `prompts.analyze.PROMPT_VERSION` so a future prompt change's
  effect on the pass rate is traceable.

An LLM-as-judge scorer was deliberately not implemented — it would add
cost, latency, and its own reliability problems (the judge model can itself
be wrong or inconsistent) without a concrete current need beyond the
rule-based signal.

## Consequences

- The evaluation harness never runs the real API unless a developer
  explicitly opts in and has credentials configured — no surprise cost, no
  network dependency in normal test runs or CI without a key.
- Quality signal is currently limited to structural/format compliance
  (keyword count, length bounds), not semantic quality (e.g. "is this
  summary actually accurate/relevant"). Semantic scoring — an LLM-as-judge
  step, or human-reviewed reference summaries — is out of scope for this
  ADR and would be a deliberate future addition if the project's learning
  goals require it, not an implicit gap to silently fill later.
- The golden dataset (15 examples as of Phase 8) is small; the pass-rate
  signal is correspondingly noisy. Expanding it is a low-risk, backward
  compatible change (append more `.jsonl` lines) if warranted.
