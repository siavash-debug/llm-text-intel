# LLM Text Intelligence

A small, production-oriented application that takes text input and uses an LLM
to produce structured output: **title**, **summary**, **keywords**.

This is primarily an LLM engineering learning project. It exists to
demonstrate, in a real codebase: LLM API integration, prompt engineering,
structured outputs, schema validation, bounded retries with error taxonomy,
LLM evaluation and prompt regression testing, observability, and cost/latency
awareness.

## Status

Phases 0-9 complete: configuration, domain schemas, the provider-agnostic
`LLMClient` interface, a real Groq client, prompt construction, the
`analyze()` pipeline with bounded retries, a CLI interface, per-request
observability logging, a rule-based evaluation harness, and this hardening
pass. See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what each phase covered.

## Architecture

Modular monolith. Core business logic (`schemas`, `prompts`, `llm`,
`pipeline`, `observability`) is independent of any interface. The CLI
(`interfaces/cli.py`) is the first interface; a FastAPI interface can be
added later as a thin wrapper over the same `pipeline.analyze()` entry
point, without duplicating logic.

The LLM provider sits behind a small `LLMClient` interface
(`src/llm_text_intel/llm/client.py`). Groq is the first (and for now only)
implementation (`src/llm_text_intel/llm/groq_client.py`) — no other module
imports the `groq` SDK.

LLM output is treated as untrusted input throughout: it is parsed and
validated against `TextAnalysis` before use, and invalid output triggers a
bounded retry rather than being trusted as-is (see
[ADR 0003](docs/adr/0003-bounded-retry-strategy.md)). User input is treated
as untrusted too: it is placed in a single clearly delimited block in the
prompt with an explicit "this is data, not instructions" directive — a
documented mitigation for prompt injection, not a guarantee (see
`src/llm_text_intel/prompts/analyze.py` and
[ADR 0002](docs/adr/0002-no-framework-mvp.md)).

## Repository structure

```text
src/llm_text_intel/
├── config.py        # env-based Settings (GROQ_API_KEY, model, retries, limits, cost rates)
├── schemas.py        # TextAnalysis, LLMResponse (Pydantic contracts)
├── errors.py         # error taxonomy
├── prompts/           # prompt construction
├── llm/                # LLMClient protocol + GroqClient implementation
├── pipeline.py        # analyze(): orchestration, parsing, bounded retry
├── observability.py   # structured per-request logging
└── interfaces/
    └── cli.py          # CLI entry point (thin wrapper over the pipeline)

tests/unit/            # fast, deterministic, no network calls
tests/eval/             # rule-based scoring (free) + opt-in live-provider eval
eval_data/               # golden dataset for the evaluation harness
docs/adr/                 # architecture decision records
docs/phases/              # per-phase implementation notes
docs/ROADMAP.md           # project roadmap
CLAUDE.md                 # engineering rules for AI-assisted work on this repo
```

See [`docs/adr/`](docs/adr/) for the reasoning behind key architectural
decisions, and [`CLAUDE.md`](CLAUDE.md) for how development on this
repository is expected to proceed.

## Setup

```bash
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and set `GROQ_API_KEY` (see the file for
other optional overrides — model, retries, limits, cost rates).

## Usage

```bash
llm-text-intel "Some article text to analyze..."
# or, piping text in:
cat article.txt | llm-text-intel
```

Prints a JSON object with `title`, `summary`, and `keywords` on success, or
`Error: ...` on stderr with a non-zero exit code on failure. Structured
per-request logs (latency, token counts, estimated cost, retry count,
outcome — never raw input/output text or the API key) are written to
stderr as JSON lines.

## Testing

```bash
ruff check .
pytest tests/unit tests/eval/test_scoring.py   # fast, deterministic, no network calls, no cost
```

The live evaluation check makes real calls to the Groq API against the
golden dataset and costs money — it is excluded from the commands above and
must be run explicitly, with `GROQ_API_KEY` exported in your shell
environment (a `.env` file alone is not enough — the skip check only looks
at the process environment):

```bash
pytest tests/eval -m eval -v
```

It is skipped automatically if `GROQ_API_KEY` is not exported.
