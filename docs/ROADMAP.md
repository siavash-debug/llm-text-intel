# Roadmap

Where the project is going. For engineering rules, see [`CLAUDE.md`](../CLAUDE.md);
for what each phase contains, see [`docs/phases/`](phases/); for the
reasoning behind key decisions, see [`docs/adr/`](adr/).

Phases are implemented strictly in order, one at a time, each requiring
explicit approval before the next begins.

## Completed

| Phase | Title | Summary |
|---|---|---|
| 0 | Repository Skeleton & Tooling | Package skeleton, `pyproject.toml`, `.gitignore`, `.env.example`, README, initial ADRs. |
| 1 | Configuration & Domain Schemas | Env-based `Settings`, `TextAnalysis`/`LLMResponse` Pydantic contracts, initial error taxonomy. |
| 2 | LLM Client Interface + Fake Implementation | Provider-agnostic `LLMClient` protocol and a `FakeLLMClient` test double. |
| 3 | Groq LLM Client | Real `GroqClient` implementation behind `LLMClient`; config switched to Groq (`GROQ_API_KEY`, `llama-3.3-70b-versatile`). |
| 4 | Prompt Builder | Pure, versioned prompt construction (`build_analyze_prompt`) with a delimited-block prompt-injection mitigation. |
| — | Documentation & Claude discipline layer | `CLAUDE.md`, this roadmap, `docs/phases/`, README consistency pass. No application/business logic changes. |
| 5 | Pipeline: Orchestration, Parsing, Bounded Retry | `pipeline.analyze()`: input validation, prompt building, LLM call, output parsing/validation, bounded retries (see [ADR 0003](adr/0003-bounded-retry-strategy.md)). |
| 6 | CLI Interface | `interfaces/cli.py`, a thin wrapper over `pipeline.analyze()`; registered as the `llm-text-intel` console script. |
| 7 | Observability | `observability.analyze_with_observability()`: one structured log record per request (latency, tokens, estimated cost, retry count, outcome), never raw text or secrets. |
| 8 | Evaluation Harness | `tests/eval/`: rule-based scoring (free, deterministic) plus an opt-in live-provider check against `eval_data/golden_set.jsonl`, tied to `PROMPT_VERSION` (see [ADR 0004](adr/0004-evaluation-approach.md)). |
| 9 | Hardening & Documentation Pass | Edge-case tests (unicode/emoji, control characters, boundary lengths), pipeline-level prompt-injection tests, ADR 0003/0004, README finalization, this roadmap correction. |

Details for each: [`docs/phases/`](phases/) (currently covers phases 0-4;
phases 5-9 are documented in their Git history and PR/commit messages).

## Current

None — Phase 9 is the last phase currently planned in detail. The project
is in a stable, documented, portfolio-presentable state.

## Upcoming

Not yet planned in detail, and not started:

- A FastAPI interface — explicitly deferred, to be added later as a thin
  wrapper reusing the same core, per [ADR 0001](adr/0001-modular-monolith.md).
- Any persistence layer — no current requirement, see
  [ADR 0002](adr/0002-no-framework-mvp.md).
- Semantic (LLM-as-judge) evaluation scoring — deliberately out of scope
  for the current rule-based evaluation harness, see
  [ADR 0004](adr/0004-evaluation-approach.md).

Further phases beyond these will be scoped and approved individually when
work on them actually begins, following the same phase-by-phase discipline
as phases 0-9.
