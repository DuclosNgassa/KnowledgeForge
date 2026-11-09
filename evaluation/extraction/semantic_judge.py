import json

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.settings import settings
from evaluation.extraction.schemas import (
    FindingJudgeResponse,
    MetricScores,
)

SYSTEM_PROMPT = """
You are an expert evaluator of structured information extraction.

Your task is to compare expected key findings with predicted key findings.

Rules:

1. Two findings are equivalent when they communicate substantially the
   same factual information.
2. Ignore differences in wording, grammar, sentence structure and style.
3. Do not consider findings equivalent if they contradict each other.
4. Do not consider findings equivalent if one introduces important
   information that is unsupported by the other.
5. Preserve important details such as names, dates, quantities,
   relationships and technical facts.
6. Each expected finding can match at most one predicted finding.
7. Each predicted finding can match at most one expected finding.
8. Prefer the strongest semantic match.
9. Do not invent matches.
10. Return only the structured result.

A predicted finding that is not supported by any expected finding
must remain unmatched.
"""


class SemanticFindingEvaluator:

    def __init__(self):
        self.model = init_chat_model(
            settings.openai_chat_model,
            temperature=0,
        ).with_structured_output(FindingJudgeResponse)

    async def evaluate(
            self,
            expected: list[str],
            predicted: list[str],
    ) -> MetricScores:

        if not expected and not predicted:
            return MetricScores(
                precision=1.0,
                recall=1.0,
                f1=1.0,
            )

        if not expected:
            return MetricScores(
                precision=0.0,
                recall=1.0,
                f1=0.0,
            )

        if not predicted:
            return MetricScores(
                precision=1.0,
                recall=0.0,
                f1=0.0,
            )

        judge_result = await self.model.ainvoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(
                    content=json.dumps(
                        {
                            "expected_findings": expected,
                            "predicted_findings": predicted,
                        },
                        ensure_ascii=False,
                    )
                ),
            ]
        )

        self._validate_matches(
            judge_result,
            expected_count=len(expected),
            predicted_count=len(predicted),
        )

        true_positives = sum(
            1
            for match in judge_result.matches
            if match.is_equivalent
        )

        false_positives = len(predicted) - true_positives
        false_negatives = len(expected) - true_positives

        precision = (
            true_positives / (true_positives + false_positives)
            if true_positives + false_positives > 0
            else 1.0
        )

        recall = (
            true_positives / (true_positives + false_negatives)
            if true_positives + false_negatives > 0
            else 1.0
        )

        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )

        return MetricScores(
            precision=precision,
            recall=recall,
            f1=f1,
        )

    @staticmethod
    def _validate_matches(
            result: FindingJudgeResponse,
            expected_count: int,
            predicted_count: int,
    ) -> None:

        expected_indices = set()
        predicted_indices = set()

        for match in result.matches:

            if match.expected_index >= expected_count:
                raise ValueError(
                    f"Invalid expected finding index: {match.expected_index}"
                )

            if match.predicted_index >= predicted_count:
                raise ValueError(
                    f"Invalid predicted finding index: {match.predicted_index}"
                )

            if match.expected_index in expected_indices:
                raise ValueError(
                    "Judge returned duplicate expected finding matches."
                )

            if match.predicted_index in predicted_indices:
                raise ValueError(
                    "Judge returned duplicate predicted finding matches."
                )

            expected_indices.add(match.expected_index)
            predicted_indices.add(match.predicted_index)
