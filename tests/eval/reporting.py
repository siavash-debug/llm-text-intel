"""Deterministic, human-readable formatting for an EvalReport.

Pure string formatting only: no I/O, no LLM/API calls. Kept separate from
test_eval_suite.py so it can be unit-tested with constructed EvalReport/
ExampleResult objects, without needing a real evaluation run.
"""

from tests.eval.scoring import EvalReport


def format_summary(report: EvalReport, *, model: str, threshold: float) -> str:
    """Render a concise, deterministic summary of an evaluation report.

    Always includes the exact aggregate counts and an explicit statement of
    per-example failures (or "none") - regardless of whether the report as
    a whole passed the threshold. Never includes example text, prompts, or
    full model responses; only example ids and short failure reasons.
    """
    failed_results = [r for r in report.results if not r.passed]

    lines = [
        "Evaluation summary",
        f"Model: {model}",
        f"Prompt version: {report.prompt_version}",
        f"Examples: {report.total}",
        f"Passed: {report.passed}",
        f"Failed: {len(failed_results)}",
        f"Pass rate: {report.pass_rate:.2%}",
        f"Threshold: {threshold:.2%}",
    ]

    if not failed_results:
        lines.append("Failures: none")
    else:
        lines.append("Failures:")
        for result in failed_results:
            reason = "; ".join(result.failures) if result.failures else "unspecified"
            lines.append(f"- {result.example_id}: {reason}")

    return "\n".join(lines)
