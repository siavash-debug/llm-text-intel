# 0005. Keyword-count contract: align evaluation to the production schema (1-15)

## Status

Accepted

## Context

Three separate places in the repository described the keyword-count contract
differently:

- **Production schema** (`src/llm_text_intel/schemas.py`,
  `TextAnalysis.keywords`): `min_length=1, max_length=15`.
- **Prompt** (`src/llm_text_intel/prompts/analyze.py`): instructs the model
  to return "a list of 1 to 15 keywords or key phrases."
- **Evaluation** (`eval_data/golden_set.jsonl`): every example specified
  `min_keywords: 2, max_keywords: 8`.

No ADR, phase document, or commit message anywhere in the repository ever
justified `8` as an intentional product requirement, an industry
convention, or a deliberate placeholder — it was undocumented.
[`docs/phases/phase-1.md`](../phases/phase-1.md) had explicitly described
the *schema's* keyword-count bound as "provisional... pending observation
of real LLM output in later phases," signaling that the schema/prompt's
1-15 range, not the evaluation's 2-8 range, was the value earmarked for
empirical validation.

The project's first live evaluation baseline (against `openai/gpt-oss-120b`,
`PROMPT_VERSION=1`) produced a pass rate of **1/15 = 6.67%**. All 14
failures were caused solely by keyword count: the model returned 9-12
keywords per example, which is valid against the production schema and
the prompt's own instructions, but fell outside the evaluation's 2-8
window. Every output was otherwise schema-valid — no provider failure,
no application failure, no parsing/schema failure.

A dedicated read-only analysis (prior to this change) confirmed:

- the schema does not enforce 2-8 anywhere,
- the prompt does not instruct the model toward 2-8,
- the 2-8 bound existed only as an evaluation-layer assumption, and
- there was no repository evidence that 8 was ever an intentional product
  target.

The human product owner was presented with three candidate contracts
(strict bounded, e.g. 2-8; broad bounded, e.g. 1-15; quality-oriented,
semantically scored) and explicitly decided the MVP contract.

## Decision

The MVP keyword-count contract is **1-15 keywords**:

- **Minimum: 1**
- **Maximum: 15**
- This is a **hard production constraint**, enforced by
  `TextAnalysis.keywords` (unchanged — it already enforced this).
- Keyword **relevance and non-redundancy remain soft requirements only**
  for the MVP — expressed as prose in the prompt ("keywords or key phrases
  from the text"), not machine-checked.
- **Semantic keyword-quality evaluation (e.g. an LLM-as-judge step) remains
  explicitly out of scope for the MVP**, consistent with
  [ADR 0004](0004-evaluation-approach.md)'s existing decision to defer
  semantic scoring — this ADR does not reopen that decision.

The evaluation golden set (`eval_data/golden_set.jsonl`) is updated so
every example's `min_keywords`/`max_keywords` match this contract (1/15),
replacing the previous, undocumented 2/8 values.

**This decision is explicitly not based on optimizing for `gpt-oss-120b`'s
observed behavior.** The contract was chosen because it matches the
existing, already-committed production schema and prompt — both of which
predate this baseline run and were never changed to fit it. The evaluation
was misaligned with an existing product contract; this decision corrects
that misalignment, it does not create a new contract to fit a model.

## Distinction: production constraint vs. evaluation heuristic

This ADR reaffirms a distinction already implicit in the codebase but not
previously stated explicitly:

- A **production constraint** (`TextAnalysis`) is what the application
  itself will accept as valid output — enforced by Pydantic validation,
  checked on every real request, and (via bounded retry, see
  [ADR 0003](0003-bounded-retry-strategy.md)) actively drives retry
  behavior when violated.
- An **evaluation heuristic** (`tests/eval/scoring.py` +
  `golden_set.jsonl`) is a deterministic proxy the project uses to get a
  repeatable quality signal. It may be *narrower* than the production
  constraint if there's a documented reason to hold the evaluation to a
  stricter bar — but when it is narrower *without* a documented reason, as
  was the case here, that is evaluation drift, not a meaningful quality
  bar.

## Consequences

- `eval_data/golden_set.jsonl` keyword bounds now match
  `TextAnalysis`/the prompt exactly; no schema, prompt, or pipeline code
  changed.
- `MIN_PASS_RATE = 0.80` in `tests/eval/test_eval_suite.py` is unchanged —
  this ADR corrects what is being measured, not how strict the pass bar is.
- The prior baseline (1/15 = 6.67% against `openai/gpt-oss-120b`) is
  **superseded by this contract correction, not invalidated as a
  measurement** — it correctly measured conformance to the *old* (2-8)
  metric; it was never a measurement of the model's actual quality against
  the approved product contract. No claim is made here about how
  `gpt-oss-120b` (or any model) would score against the corrected 1-15
  metric — that requires a new evaluation run, which is out of scope for
  this ADR.
- Still open, not addressed by this decision: keyword semantic
  quality/relevance/redundancy remain unevaluated; the title/summary
  evaluation metric (word count) still uses different units than the
  production schema (character count) — both are tracked as separate,
  still-undecided gaps.
