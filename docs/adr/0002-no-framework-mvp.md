# 0002. Avoid frameworks, microservices, async, and a database for the MVP

## Status

Accepted

## Context

It would be possible to reach for an LLM orchestration framework
(LangChain-style), a web framework from day one, async processing, or a
database to persist results. None of these are required to satisfy the
functional requirements (text in, structured result out) or the learning
goals of this project. The explicit goal is to understand and demonstrate
LLM API integration, retries, and validation directly — a framework would
hide exactly what this project exists to teach.

## Decision

For the MVP:

- No LLM orchestration framework. The LLM client is a small hand-written
  interface (see ADR 0003, once written) around the Groq SDK.
- No web framework yet. CLI is the first interface.
- No async processing. Requests are synchronous, single-request-at-a-time.
- No database. Results are returned to the caller (CLI stdout); nothing is
  persisted.
- No premature multi-provider abstraction beyond what a clean interface
  boundary already gives us for free.

## Consequences

- Less code hidden behind abstractions; every retry, validation, and error
  path is visible and testable in this codebase.
- Revisiting this decision is expected as the project evolves — e.g. a
  FastAPI interface is explicitly planned for later, and persistence may be
  added if the product requires result history. Each such addition should
  get its own ADR when it happens, justified by an actual requirement.
