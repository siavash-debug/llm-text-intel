# 0001. Modular monolith, not microservices

## Status

Accepted

## Context

The application has a single deployable concern: accept text, produce a
structured LLM-derived result (title/summary/keywords). The project is a
solo learning project with one team and no independent scaling or
deployment requirements between its parts.

## Decision

Build a single Python package organized into clearly separated modules
(config, schemas, prompts, llm client, pipeline, observability, interfaces),
rather than splitting into separate services.

Core business logic (`pipeline`, `schemas`, `prompts`, `llm`) is kept
independent of any interface. Interfaces (CLI now, FastAPI later) are thin
wrappers that only wire configuration and a client together and call the
core's public entry point.

## Consequences

- No network/deployment/versioning overhead between components.
- Module boundaries are enforced by import discipline and code review, not
  by process/network isolation.
- Adding a second interface (e.g. FastAPI) later requires no change to core
  logic — only a new thin wrapper module.
- If this project ever needed independent scaling or deployment of a part
  (e.g. a separate long-running worker), that would be a reason to revisit
  this decision — no such need exists today.
