# LLM Text Intelligence

A small, production-oriented application that takes text input and uses an LLM
to produce structured output: **title**, **summary**, **keywords**.

This is primarily an LLM engineering learning project. It exists to
demonstrate, in a real codebase: LLM API integration, prompt engineering,
structured outputs, schema validation, bounded retries with error taxonomy,
LLM evaluation and prompt regression testing, observability, and cost/latency
awareness.

## Status

Phases 0-4 complete: configuration, domain schemas, the provider-agnostic
`LLMClient` interface, a real Groq client, and prompt construction. No
orchestration pipeline or interface (CLI) yet — see
[`docs/ROADMAP.md`](docs/ROADMAP.md) for what's done and what's next.

## Architecture

Modular monolith. Core business logic (`schemas`, `prompts`, `llm`, and a
future `pipeline`) is independent of any interface. A CLI will be the first
interface; a FastAPI interface can be added later as a thin wrapper over the
same pipeline entry point, without duplicating logic.

The LLM provider sits behind a small `LLMClient` interface
(`src/llm_text_intel/llm/client.py`). Groq is the first (and for now only)
implementation (`src/llm_text_intel/llm/groq_client.py`) — no other module
imports the `groq` SDK.

## Repository structure

```text
src/llm_text_intel/
├── config.py       # env-based Settings (GROQ_API_KEY, model, retries, limits)
├── schemas.py       # TextAnalysis, LLMResponse (Pydantic contracts)
├── errors.py        # error taxonomy
├── prompts/          # prompt construction
└── llm/              # LLMClient protocol + GroqClient implementation

tests/unit/           # fast, no network calls
docs/adr/              # architecture decision records
docs/phases/           # per-phase implementation notes
docs/ROADMAP.md        # project roadmap
CLAUDE.md              # engineering rules for AI-assisted work on this repo
```

See [`docs/adr/`](docs/adr/) for the reasoning behind key architectural
decisions, and [`CLAUDE.md`](CLAUDE.md) for how development on this
repository is expected to proceed.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

Copy `.env.example` to `.env` and set `GROQ_API_KEY` before running
anything that calls the real API.
