"""Golden-set evaluation against the real Groq pipeline.

This is an opt-in, non-deterministic, costs-money integration check, not a
unit test: it makes real network calls and is excluded from the default
unit test run (`pytest tests/unit`). Run explicitly with:

    pytest tests/eval -m eval -v

Requires a real GROQ_API_KEY in the environment; skipped automatically
otherwise (e.g. in CI without credentials configured).
"""

import os
from pathlib import Path

import pytest

from llm_text_intel.config import load_settings
from llm_text_intel.llm.groq_client import GroqClient
from llm_text_intel.pipeline import analyze
from llm_text_intel.prompts.analyze import PROMPT_VERSION
from tests.eval.reporting import format_summary
from tests.eval.scoring import build_report, load_golden_set, score_example

GOLDEN_SET_PATH = Path(__file__).resolve().parents[2] / "eval_data" / "golden_set.jsonl"
MIN_PASS_RATE = 0.8

pytestmark = pytest.mark.eval


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY"), reason="requires a real GROQ_API_KEY in the environment"
)
def test_golden_set_pass_rate_meets_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    settings = load_settings()
    client = GroqClient(api_key=settings.groq_api_key, model=settings.model_name)
    examples = load_golden_set(GOLDEN_SET_PATH)

    results = [
        score_example(example, analyze(example.text, client=client, settings=settings))
        for example in examples
    ]
    report = build_report(PROMPT_VERSION, results)

    summary = format_summary(report, model=settings.model_name, threshold=MIN_PASS_RATE)
    # capsys.disabled() writes straight to the real stdout, bypassing
    # pytest's capture, so this is visible under `pytest -m eval -v`
    # whether the test passes or fails - not just on failure.
    with capsys.disabled():
        print(f"\n{summary}\n")

    assert report.pass_rate >= MIN_PASS_RATE, (
        f"eval pass rate {report.pass_rate:.2%} below threshold {MIN_PASS_RATE:.0%} "
        f"(prompt_version={report.prompt_version})"
    )
