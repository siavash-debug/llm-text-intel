from pathlib import Path

from llm_text_intel.schemas import TextAnalysis
from tests.eval.scoring import (
    GoldenExample,
    build_report,
    load_golden_set,
    score_example,
)

GOLDEN_SET_PATH = Path(__file__).resolve().parents[2] / "eval_data" / "golden_set.jsonl"


def _example(**overrides: object) -> GoldenExample:
    defaults = {
        "id": "ex-1",
        "text": "some text",
        "min_keywords": 2,
        "max_keywords": 5,
        "max_title_words": 10,
        "max_summary_words": 30,
    }
    defaults.update(overrides)
    return GoldenExample(**defaults)  # type: ignore[arg-type]


def _analysis(
    title: str = "Short Title",
    summary: str = "A short summary.",
    keywords: list[str] | None = None,
) -> TextAnalysis:
    return TextAnalysis(title=title, summary=summary, keywords=keywords or ["a", "b", "c"])


class TestScoreExample:
    def test_passing_analysis_is_scored_as_passed(self) -> None:
        result = score_example(_example(), _analysis())
        assert result.passed is True
        assert result.failures == []

    def test_too_few_keywords_fails(self) -> None:
        result = score_example(_example(min_keywords=3), _analysis(keywords=["a"]))
        assert result.passed is False
        assert any("keyword count" in f for f in result.failures)

    def test_too_many_keywords_fails(self) -> None:
        result = score_example(
            _example(max_keywords=2), _analysis(keywords=["a", "b", "c", "d"])
        )
        assert result.passed is False
        assert any("keyword count" in f for f in result.failures)

    def test_title_too_long_fails(self) -> None:
        result = score_example(
            _example(max_title_words=2), _analysis(title="This Title Has Too Many Words")
        )
        assert result.passed is False
        assert any("title word count" in f for f in result.failures)

    def test_summary_too_long_fails(self) -> None:
        result = score_example(
            _example(max_summary_words=3),
            _analysis(summary="This summary has far too many words in it"),
        )
        assert result.passed is False
        assert any("summary word count" in f for f in result.failures)

    def test_result_carries_example_id(self) -> None:
        result = score_example(_example(id="custom-id"), _analysis())
        assert result.example_id == "custom-id"


class TestBuildReport:
    def test_all_passing_gives_full_pass_rate(self) -> None:
        example = _example()
        results = [score_example(example, _analysis()) for _ in range(3)]
        report = build_report("1", results)

        assert report.total == 3
        assert report.passed == 3
        assert report.pass_rate == 1.0

    def test_mixed_results_computes_partial_pass_rate(self) -> None:
        good = score_example(_example(), _analysis())
        bad = score_example(_example(min_keywords=5), _analysis(keywords=["a"]))
        report = build_report("1", [good, bad])

        assert report.total == 2
        assert report.passed == 1
        assert report.pass_rate == 0.5

    def test_empty_results_has_zero_pass_rate_not_division_error(self) -> None:
        report = build_report("1", [])
        assert report.total == 0
        assert report.pass_rate == 0.0

    def test_report_carries_prompt_version(self) -> None:
        report = build_report("42", [])
        assert report.prompt_version == "42"


class TestKeywordContractAlignment:
    """Regression coverage for the 1-15 keyword contract (ADR 0005).

    Confirms the golden set's keyword bounds match the production
    TextAnalysis schema (1-15) exactly, and that score_example accepts the
    full 1-15 range at its boundaries - guarding against the evaluation
    silently drifting narrower than the schema again.
    """

    def test_golden_set_keyword_bounds_match_the_production_contract(self) -> None:
        examples = load_golden_set(GOLDEN_SET_PATH)
        assert examples, "golden set must not be empty"
        for example in examples:
            assert example.min_keywords == 1, example.id
            assert example.max_keywords == 15, example.id

    def test_minimum_contract_keyword_count_passes(self) -> None:
        contract = _example(min_keywords=1, max_keywords=15)
        analysis = _analysis(keywords=["only-keyword"])
        result = score_example(contract, analysis)
        assert result.passed is True

    def test_maximum_contract_keyword_count_passes(self) -> None:
        contract = _example(min_keywords=1, max_keywords=15)
        analysis = _analysis(keywords=[f"kw{i}" for i in range(15)])
        result = score_example(contract, analysis)
        assert result.passed is True

    def test_below_contract_minimum_fails(self) -> None:
        # TextAnalysis itself forbids 0 keywords (schema min_length=1), so
        # "below contract" is exercised via a stricter example contract
        # (min_keywords=2) rather than an unconstructable TextAnalysis.
        contract = _example(min_keywords=2, max_keywords=15)
        analysis = _analysis(keywords=["only-one"])
        result = score_example(contract, analysis)
        assert result.passed is False

    def test_above_contract_maximum_fails(self) -> None:
        # TextAnalysis itself forbids 16 keywords (schema max_length=15), so
        # "above contract" is exercised via a stricter example contract
        # (max_keywords=14) rather than an unconstructable TextAnalysis.
        contract = _example(min_keywords=1, max_keywords=14)
        analysis = _analysis(keywords=[f"kw{i}" for i in range(15)])
        result = score_example(contract, analysis)
        assert result.passed is False


class TestLoadGoldenSet:
    def test_loads_the_real_golden_set_file(self) -> None:
        examples = load_golden_set(GOLDEN_SET_PATH)

        assert len(examples) >= 15
        assert all(isinstance(e, GoldenExample) for e in examples)

    def test_all_example_ids_are_unique(self) -> None:
        examples = load_golden_set(GOLDEN_SET_PATH)
        ids = [e.id for e in examples]
        assert len(ids) == len(set(ids))

    def test_all_examples_have_nonempty_text(self) -> None:
        examples = load_golden_set(GOLDEN_SET_PATH)
        assert all(e.text.strip() for e in examples)
