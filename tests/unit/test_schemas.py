import pytest
from pydantic import ValidationError

from llm_text_intel.schemas import LLMResponse, TextAnalysis


class TestTextAnalysis:
    def test_valid_construction(self) -> None:
        analysis = TextAnalysis(
            title="A Title",
            summary="A short summary.",
            keywords=["one", "two"],
        )
        assert analysis.title == "A Title"
        assert analysis.keywords == ["one", "two"]

    def test_empty_title_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TextAnalysis(title="", summary="summary", keywords=["k"])

    def test_empty_summary_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TextAnalysis(title="Title", summary="", keywords=["k"])

    def test_empty_keywords_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TextAnalysis(title="Title", summary="summary", keywords=[])

    def test_missing_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TextAnalysis(title="Title", summary="summary")  # type: ignore[call-arg]

    def test_title_too_long_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TextAnalysis(title="x" * 201, summary="summary", keywords=["k"])

    def test_too_many_keywords_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TextAnalysis(title="Title", summary="summary", keywords=[f"k{i}" for i in range(16)])

    def test_is_frozen(self) -> None:
        analysis = TextAnalysis(title="Title", summary="summary", keywords=["k"])
        with pytest.raises(ValidationError):
            analysis.title = "New Title"  # type: ignore[misc]


class TestLLMResponse:
    def test_valid_construction(self) -> None:
        response = LLMResponse(
            text='{"title": "t"}',
            input_tokens=10,
            output_tokens=5,
            model="claude-sonnet-5",
        )
        assert response.input_tokens == 10

    def test_negative_tokens_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LLMResponse(text="x", input_tokens=-1, output_tokens=5, model="m")

    def test_empty_model_rejected(self) -> None:
        with pytest.raises(ValidationError):
            LLMResponse(text="x", input_tokens=1, output_tokens=1, model="")

    def test_zero_tokens_allowed(self) -> None:
        response = LLMResponse(text="x", input_tokens=0, output_tokens=0, model="m")
        assert response.input_tokens == 0
