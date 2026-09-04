"""Rule-based scoring of TextAnalysis outputs against golden-set expectations.

No LLM calls happen in this module — it only loads static expectations and
compares an already-produced TextAnalysis against them. This is the free,
deterministic half of the evaluation harness; test_eval_suite.py is the
half that actually calls the real pipeline/provider.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from llm_text_intel.schemas import TextAnalysis


@dataclass(frozen=True)
class GoldenExample:
    id: str
    text: str
    min_keywords: int
    max_keywords: int
    max_title_words: int
    max_summary_words: int


@dataclass(frozen=True)
class ExampleResult:
    example_id: str
    passed: bool
    failures: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvalReport:
    prompt_version: str
    results: list[ExampleResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


def load_golden_set(path: Path) -> list[GoldenExample]:
    """Load golden examples from a JSON Lines file (one example per line)."""
    examples = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            examples.append(GoldenExample(**json.loads(line)))
    return examples


def score_example(example: GoldenExample, analysis: TextAnalysis) -> ExampleResult:
    """Score a TextAnalysis against one golden example's rule-based expectations."""
    failures: list[str] = []

    keyword_count = len(analysis.keywords)
    if not (example.min_keywords <= keyword_count <= example.max_keywords):
        failures.append(
            f"keyword count {keyword_count} outside "
            f"[{example.min_keywords}, {example.max_keywords}]"
        )

    title_words = len(analysis.title.split())
    if title_words > example.max_title_words:
        failures.append(f"title word count {title_words} exceeds {example.max_title_words}")

    summary_words = len(analysis.summary.split())
    if summary_words > example.max_summary_words:
        failures.append(
            f"summary word count {summary_words} exceeds {example.max_summary_words}"
        )

    return ExampleResult(example_id=example.id, passed=not failures, failures=failures)


def build_report(prompt_version: str, results: list[ExampleResult]) -> EvalReport:
    return EvalReport(prompt_version=prompt_version, results=results)
