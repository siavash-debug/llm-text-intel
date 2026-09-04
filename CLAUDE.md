# CLAUDE.md

Durable engineering instructions for Claude (or any agent) working on this
repository. This file governs *how* work happens here. See
[`docs/ROADMAP.md`](docs/ROADMAP.md) for *where the project is going*,
[`docs/phases/`](docs/phases/) for *what each phase contains*, and
[`docs/adr/`](docs/adr/) for *why* key decisions were made.

## Project context

**LLM Text Intelligence** takes text input and uses an LLM to produce
structured output: `title`, `summary`, `keywords`. It is primarily an LLM
engineering learning project — the goal is to demonstrate sound practice in
LLM API integration, prompt engineering, structured outputs, schema
validation, bounded retries, evaluation, observability, and security, not
to maximize feature scope.

**Architecture:** modular monolith. Core business logic is independent of
any interface (CLI first; a FastAPI interface may be added later without
duplicating logic).

**LLM provider:** Groq (`groq` SDK), accessed only through
`llm_text_intel.llm.groq_client.GroqClient`. The rest of the application
depends solely on the provider-agnostic `llm_text_intel.llm.client.LLMClient`
protocol and `llm_text_intel.schemas.LLMResponse` — no file outside
`llm/groq_client.py` may import the `groq` package or depend on its types.

**Directory structure (current):**

```text
src/llm_text_intel/
├── config.py        # env-based Settings (GROQ_API_KEY, model, retries, limits, cost rates)
├── schemas.py        # TextAnalysis, LLMResponse (Pydantic contracts)
├── errors.py         # AnalysisError taxonomy
├── prompts/           # pure prompt construction (analyze.py)
├── llm/                # LLMClient protocol + GroqClient implementation
├── pipeline.py        # analyze(): orchestration, parsing, bounded retry
├── observability.py   # structured per-request logging
└── interfaces/
    └── cli.py          # CLI entry point (thin wrapper over the pipeline)

tests/
├── unit/              # fast, deterministic, no network calls
└── eval/               # rule-based scoring (free) + opt-in live-provider eval

eval_data/               # golden dataset for the evaluation harness
```

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's planned beyond this.

## Engineering principles

- MVP-first: implement the minimal thing that satisfies the current phase.
- Avoid speculative abstractions — no interface, config option, or module
  exists "for later" unless a concrete, already-approved future phase needs
  it (e.g. `PROMPT_VERSION` exists now because Phase 8's eval work needs it).
- Keep provider-specific SDK code isolated inside its client module.
- Prefer explicit, typed contracts (Pydantic models, `Protocol`s) and small,
  single-responsibility modules over frameworks or generic abstractions.
- No unnecessary frameworks (no LLM orchestration framework, no web
  framework until an interface phase actually needs one).
- Do not add a dependency without a concrete, current need.
- Keep all core logic unit-testable without a network connection.
- No real network calls in unit tests — mock/fake at the `LLMClient` or SDK
  boundary.

## Scope discipline

- Work only within the explicitly approved phase.
- Do not silently implement future-phase functionality, even if it looks
  convenient or "would be useful now."
- Do not expand scope opportunistically.
- If a change looks necessary but belongs to a different phase, record it
  as a risk/deferred item in that phase's report or doc — do not implement
  it speculatively.
- Do not proceed to the next phase without explicit user approval.

## Testing and validation

Before declaring any phase successful:

1. Run the tests relevant to the phase.
2. Run the full test suite.
3. Run Ruff.
4. Perform an import/sanity check when appropriate.
5. Review the resulting `git diff`.
6. Check for unrelated changes.
7. Check for secrets and generated/build files.
8. Self-review for unnecessary complexity.

A phase is not complete if any validation step fails.

## Secrets and configuration

- Never hard-code API keys or credentials.
- Never commit `.env`.
- `.env.example` may contain variable names/placeholders only, no real values.
- Check staged files before every commit.
- Never commit secrets, credentials, caches, build artifacts, or generated
  files (`__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `.ruff_cache/`).

## Git / Phase Completion Protocol

```text
Implement approved phase
        |
Run tests
        |
Run full test suite
        |
Run Ruff
        |
Self-review
        |
Review git diff/status
        |
Check secrets/generated files
        |
All validation passes?
   +-- NO  -> fix -> validate again
   +-- YES
        |
git add -A
        |
Review staged diff
        |
git commit
        |
git push
        |
Verify local HEAD == remote HEAD
        |
Verify working tree is clean
        |
Report completion
        |
STOP and wait for explicit approval
```

Rules:

- Do not commit if tests or lint fail.
- Do not push if the commit contains unrelated changes.
- Use clear Conventional Commit messages (`feat:`, `fix:`, `docs:`, `test:`, ...).
- One logical phase should normally result in one final commit.
- Never push secrets.
- After a successful push, stop. Never automatically begin the next phase.
- User approval is required before starting every subsequent phase.
