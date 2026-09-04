# LLM Text Intelligence

A small, production-oriented application that takes text input and uses an LLM
to produce structured output: **title**, **summary**, **keywords**.

This is primarily an LLM engineering learning project. It exists to
demonstrate, in a real codebase: LLM API integration, prompt engineering,
structured outputs, schema validation, bounded retries with error taxonomy,
LLM evaluation and prompt regression testing, observability, and cost/latency
awareness.

## Status

Early scaffolding (Phase 0). No business logic yet.

## Architecture

Modular monolith. Core business logic (`pipeline`, `schemas`, `prompts`,
`llm`) is independent of any interface. The CLI (`interfaces/cli.py`) is the
first interface; a FastAPI interface can be added later as a thin wrapper
over the same `pipeline.analyze()` entry point, without duplicating logic.

The LLM provider sits behind a small `LLMClient` interface. Groq is the
first (and for now only) implementation.

See [`docs/adr/`](docs/adr/) for the reasoning behind these decisions.

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

Copy `.env.example` to `.env` and set `GROQ_API_KEY` before running
anything that calls the real API.
