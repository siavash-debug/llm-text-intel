from tests.eval.reporting import format_summary
from tests.eval.scoring import EvalReport, ExampleResult


def _passing(example_id: str) -> ExampleResult:
    return ExampleResult(example_id=example_id, passed=True, failures=[])


def _failing(example_id: str, *failures: str) -> ExampleResult:
    return ExampleResult(example_id=example_id, passed=False, failures=list(failures))


class TestFormatSummaryAllPassing:
    def test_reports_exact_aggregate_counts(self) -> None:
        report = EvalReport(prompt_version="1", results=[_passing("a"), _passing("b")])
        summary = format_summary(report, model="openai/gpt-oss-120b", threshold=0.8)

        assert "Model: openai/gpt-oss-120b" in summary
        assert "Prompt version: 1" in summary
        assert "Examples: 2" in summary
        assert "Passed: 2" in summary
        assert "Failed: 0" in summary

    def test_reports_no_failures_explicitly_rather_than_omitting_the_section(self) -> None:
        report = EvalReport(prompt_version="1", results=[_passing("a")])
        summary = format_summary(report, model="m", threshold=0.8)

        assert "Failures: none" in summary
        assert "Failures:\n" not in summary

    def test_pass_rate_is_formatted_as_a_percentage(self) -> None:
        report = EvalReport(prompt_version="1", results=[_passing("a"), _passing("b")])
        summary = format_summary(report, model="m", threshold=0.8)

        assert "Pass rate: 100.00%" in summary

    def test_threshold_is_formatted_as_a_percentage(self) -> None:
        report = EvalReport(prompt_version="1", results=[_passing("a")])
        summary = format_summary(report, model="m", threshold=0.8)

        assert "Threshold: 80.00%" in summary


class TestFormatSummaryWithFailures:
    def test_reports_exact_aggregate_counts(self) -> None:
        report = EvalReport(
            prompt_version="1",
            results=[_passing("a"), _failing("b", "keyword count 20 outside [1, 15]")],
        )
        summary = format_summary(report, model="m", threshold=0.8)

        assert "Examples: 2" in summary
        assert "Passed: 1" in summary
        assert "Failed: 1" in summary

    def test_lists_each_failing_example_id_and_reason(self) -> None:
        report = EvalReport(
            prompt_version="1",
            results=[
                _failing("example-03", "summary word count 120 exceeds 100"),
                _failing("example-07", "title word count 18 exceeds 15"),
            ],
        )
        summary = format_summary(report, model="m", threshold=0.8)

        assert "- example-03: summary word count 120 exceeds 100" in summary
        assert "- example-07: title word count 18 exceeds 15" in summary

    def test_multiple_failure_reasons_for_one_example_are_joined(self) -> None:
        report = EvalReport(
            prompt_version="1",
            results=[_failing("example-01", "reason one", "reason two")],
        )
        summary = format_summary(report, model="m", threshold=0.8)

        assert "- example-01: reason one; reason two" in summary

    def test_pass_rate_reflects_partial_pass(self) -> None:
        report = EvalReport(
            prompt_version="1",
            results=[_passing("a"), _passing("b"), _passing("c"), _failing("d", "x")],
        )
        summary = format_summary(report, model="m", threshold=0.8)

        assert "Pass rate: 75.00%" in summary

    def test_does_not_include_the_word_none_when_failures_exist(self) -> None:
        report = EvalReport(prompt_version="1", results=[_failing("a", "x")])
        summary = format_summary(report, model="m", threshold=0.8)

        assert "Failures: none" not in summary


class TestFormatSummaryEdgeCases:
    def test_failure_with_no_recorded_reason_shows_unspecified(self) -> None:
        report = EvalReport(prompt_version="1", results=[_failing("a")])
        summary = format_summary(report, model="m", threshold=0.8)

        assert "- a: unspecified" in summary

    def test_output_stays_concise_per_failure_line(self) -> None:
        # format_summary's signature only accepts ids/failure strings, never
        # raw example text or model output, so there is nothing for it to
        # leak - this guards against an accidentally verbose failure line.
        report = EvalReport(
            prompt_version="1",
            results=[_failing("a", "keyword count 20 outside [1, 15]")],
        )
        summary = format_summary(report, model="m", threshold=0.8)

        failure_line = next(line for line in summary.splitlines() if line.startswith("- a:"))
        assert len(failure_line) < 200
