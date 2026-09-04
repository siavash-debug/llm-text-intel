# Phase 0 — Repository Skeleton & Tooling

**Status:** Completed

## Objective

Establish a working, installable, lintable Python package with no business
logic yet.

## Implemented work

- `pyproject.toml`: `src/`-layout package, dev dependencies (`pytest`,
  `ruff`), Ruff configuration.
- `.gitignore`, `.env.example` (placeholder variable names only).
- `README.md`: project purpose, architecture summary, dev commands.
- `src/llm_text_intel/__init__.py`.
- Initial ADRs: `docs/adr/0001-modular-monolith.md`,
  `docs/adr/0002-no-framework-mvp.md`.

## Design decisions

- `src/`-layout package over a flat script, for clean packaging/testing.
- No runtime dependencies added — nothing in this phase imports anything
  beyond the standard library.

## Tests / validation

No logic existed yet, so no tests were added. Validated via:
`pip install -e ".[dev]"`, `ruff check .`, and a plain import check.

## Dependencies introduced

None (runtime). Dev: `pytest`, `ruff`.

## Known risks / deferred items

None specific to this phase.
