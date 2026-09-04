"""CLI interface: the first interface over the core pipeline.

This module only wires configuration and a client together, calls
``pipeline.analyze``, and formats the result or error for the terminal. It
contains no business logic of its own — a future FastAPI interface would
call the same ``pipeline.analyze`` the same way (see ADR 0001).

``client``/``settings`` are accepted as optional parameters purely to allow
tests to inject a fake client and settings without touching real
environment variables or the network; the real CLI entry point
(``run()``) never passes them, so production behavior is unaffected.
"""

import argparse
import json
import sys
from collections.abc import Sequence

from llm_text_intel.config import Settings, load_settings
from llm_text_intel.errors import AnalysisError
from llm_text_intel.llm.client import LLMClient
from llm_text_intel.llm.groq_client import GroqClient
from llm_text_intel.pipeline import analyze


def main(
    argv: Sequence[str] | None = None,
    *,
    client: LLMClient | None = None,
    settings: Settings | None = None,
) -> int:
    """Run the CLI. Returns a process exit code."""
    args = _parse_args(argv)
    text = args.text if args.text is not None else sys.stdin.read()

    try:
        if settings is None:
            settings = load_settings()
        if client is None:
            client = GroqClient(api_key=settings.groq_api_key, model=settings.model_name)
        result = analyze(text, client=client, settings=settings)
    except AnalysisError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.model_dump(), indent=2))
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="llm-text-intel",
        description="Analyze text into a title, summary, and keywords using an LLM.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to analyze. If omitted, text is read from stdin.",
    )
    return parser.parse_args(argv)


def run() -> None:
    """Console-script entry point."""
    sys.exit(main())


if __name__ == "__main__":
    run()
