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

Details for each: [`docs/phases/`](phases/).

## Current

**Documentation & Claude discipline layer** (this change): `CLAUDE.md`,
this roadmap, `docs/phases/`, ADR cleanup, README consistency pass. No
application/business logic changes.

## Upcoming

Scope for these phases is as originally planned; exact implementation
details are decided when each phase is actually started, not in advance.

| Phase | Title | Intended scope (subject to refinement at start) |
|---|---|---|
| 5 | Pipeline: Orchestration, Parsing, Bounded Retry | Core `analyze()` entry point: input validation, prompt building, LLM call, output parsing/validation against `TextAnalysis`, bounded retries distinguishing transient provider failures from invalid-output failures. |
| 6 | CLI Interface | First interface (`interfaces/cli.py`), a thin wrapper over `pipeline.analyze()` with no business logic of its own. |
| 7 | Observability | Structured logging of latency, token usage, cost, retry count/reason, and outcome per request. |
| 8 | Evaluation Harness | Golden dataset, rule-based scoring, prompt-regression checks tied to `PROMPT_VERSION`. |
| 9 | Hardening & Documentation Pass | Edge-case tests, prompt-injection test cases, final README/ADR pass. |

Not yet planned in detail: a FastAPI interface (explicitly deferred, to be
added later as a thin wrapper reusing the same core, per
[ADR 0001](adr/0001-modular-monolith.md)) and any persistence layer (no
current requirement — see
[ADR 0002](adr/0002-no-framework-mvp.md)).
