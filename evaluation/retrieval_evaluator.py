import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from evaluation.schemas import EvaluationSample
from evaluation.metrics import expected_chunk_ids
import time
from cohere.errors import TooManyRequestsError

from app.observability.langfuse import langfuse


@dataclass
class RankingMetrics:
    recall_at_5: float
    precision_at_5: float
    mrr_at_20: float
    hit_at_5: float


@dataclass
class SampleRetrievalResult:
    sample_id: str
    question_type: str
    difficulty: str
    answerable: bool
    rrf: RankingMetrics | None
    reranked: RankingMetrics | None


@dataclass
class RetrievalReport:
    total_samples: int
    evaluated_samples: int
    skipped_unanswerable_samples: int
    rrf_metrics: dict[str, float]
    reranked_metrics: dict[str, float]
    results: list[SampleRetrievalResult]


HybridSearch = Callable[..., Awaitable[list[Any]]]
Rerank = Callable[..., Awaitable[list[Any]]]


def calculate_metrics(
        relevant_ids: set[str],
        ranked_ids: list[str],
        k: int = 5,
) -> RankingMetrics:
    if not relevant_ids:
        raise ValueError(
            "Cannot calculate relevance metrics without ground truth"
        )

    top_k = ranked_ids[:k]
    relevant_in_top_k = sum(
        chunk_id in relevant_ids for chunk_id in top_k
    )

    first_relevant_rank = next(
        (
            rank
            for rank, chunk_id in enumerate(ranked_ids, start=1)
            if chunk_id in relevant_ids
        ),
        None,
    )

    return RankingMetrics(
        recall_at_5=relevant_in_top_k / len(relevant_ids),
        precision_at_5=relevant_in_top_k / k,
        mrr_at_20=(
            1.0 / first_relevant_rank
            if first_relevant_rank is not None
            else 0.0
        ),
        hit_at_5=float(relevant_in_top_k > 0),
    )


def _record_sample_scores(
        span,
        sample_id: str,
        rrf_metrics,
        reranked_metrics,
) -> None:
    span.update(
        metadata={
            "evaluation_sample_id": sample_id,
        }
    )

    if rrf_metrics is not None:
        for name, value in {
            "rrf_recall_at_5": rrf_metrics.recall_at_5,
            "rrf_precision_at_5": rrf_metrics.precision_at_5,
            "rrf_mrr_at_20": rrf_metrics.mrr_at_20,
            "rrf_hit_at_5": rrf_metrics.hit_at_5,
        }.items():
            span.score(
                name=name,
                value=float(value),
                data_type="NUMERIC",
            )

    if reranked_metrics is not None:
        for name, value in {
            "reranked_recall_at_5": reranked_metrics.recall_at_5,
            "reranked_precision_at_5": reranked_metrics.precision_at_5,
            "reranked_mrr_at_20": reranked_metrics.mrr_at_20,
            "reranked_hit_at_5": reranked_metrics.hit_at_5,
        }.items():
            span.score(
                name=name,
                value=float(value),
                data_type="NUMERIC",
            )


class RetrievalEvaluator:
    def __init__(
            self,
            hybrid_search: HybridSearch,
            rerank: Rerank,
            user_id: UUID,
            candidate_k: int = 20,
            final_k: int = 5,
            min_request_interval: float = 7.2,
            max_retries: int = 3,
    ) -> None:
        if candidate_k < final_k:
            raise ValueError("candidate_k must be >= final_k")

        self.hybrid_search = hybrid_search
        self.rerank = rerank
        self.user_id = user_id
        self.candidate_k = candidate_k
        self.final_k = final_k

        self.min_request_interval = min_request_interval
        self.max_retries = max_retries

        self._last_rerank_request = 0.0
        self._rerank_lock = asyncio.Lock()

    @staticmethod
    def _chunk_ids(results: list[Any]) -> list[str]:
        # Preserve ranking order and avoid duplicate chunk IDs.
        return list(dict.fromkeys(
            str(result.chunk_id) for result in results
        ))

    async def evaluate_sample(
            self,
            sample: EvaluationSample,
    ) -> SampleRetrievalResult:
        with langfuse.start_as_current_observation(
                as_type="span",
                name="retrieval-evaluation-sample",
                input={
                    "sample_id": sample["id"],
                    "question": sample["question"],
                    "question_type": sample["question_type"],
                    "difficulty": sample["difficulty"],
                },
        ) as span:
            candidates = await self.hybrid_search(
                query=sample["question"],
                user_id=self.user_id,
                limit=self.candidate_k,
            )

            rrf_ids = self._chunk_ids(candidates)

            # Unanswerable questions are handled separately.
            if not sample["answerable"]:
                span.update(
                    output={
                        "answerable": False,
                        "rrf_chunk_ids": rrf_ids,
                    }
                )

                return SampleRetrievalResult(
                    sample_id=sample["id"],
                    question_type=sample["question_type"],
                    difficulty=sample["difficulty"],
                    answerable=False,
                    rrf=None,
                    reranked=None,
                )

            reranked = await self._rerank_with_rate_limit(
                query=sample["question"],
                results=candidates,
                top_k=self.candidate_k,
                request_id=f"eval-{sample['id']}",
            )

            reranked_ids = self._chunk_ids(reranked)
            relevant_ids = expected_chunk_ids(sample)

            rrf_metrics = calculate_metrics(
                relevant_ids,
                rrf_ids,
                self.final_k,
            )
            reranked_metrics = calculate_metrics(
                relevant_ids,
                reranked_ids,
                self.final_k,
            )

            _record_sample_scores(
                span,
                sample["id"],
                rrf_metrics,
                reranked_metrics,
            )

            span.update(
                output={
                    "answerable": True,
                    "relevant_chunk_ids": list(relevant_ids),
                    "rrf_chunk_ids": rrf_ids,
                    "reranked_chunk_ids": reranked_ids,
                }
            )

            return SampleRetrievalResult(
                sample_id=sample["id"],
                question_type=sample["question_type"],
                difficulty=sample["difficulty"],
                answerable=True,
                rrf=rrf_metrics,
                reranked=reranked_metrics,
            )

    async def evaluate(
            self,
            samples: list[EvaluationSample],
    ) -> RetrievalReport:
        with langfuse.start_as_current_observation(
                as_type="span",
                name="knowledgeforge-retrieval-evaluation",
                input={
                    "total_samples": len(samples),
                    "candidate_k": self.candidate_k,
                    "final_k": self.final_k,
                },
        ) as run_span:
            results = [
                await self.evaluate_sample(sample)
                for sample in samples
            ]

            # Reuse your existing aggregation logic here.
            evaluated = [
                result for result in results
                if result.answerable
            ]

            rrf_metrics = self._aggregate_metrics(
                [result.rrf for result in evaluated]
            )
            reranked_metrics = self._aggregate_metrics(
                [result.reranked for result in evaluated]
            )

            report = RetrievalReport(
                total_samples=len(samples),
                evaluated_samples=len(evaluated),
                skipped_unanswerable_samples=(
                        len(results) - len(evaluated)
                ),
                rrf_metrics=rrf_metrics,
                reranked_metrics=reranked_metrics,
                results=results,
            )

            # Attach aggregate metrics to the overall Langfuse trace.
            for stage, metrics in [
                ("rrf", report.rrf_metrics),
                ("reranked", report.reranked_metrics),
            ]:
                for metric_name, value in metrics.items():
                    run_span.score_trace(
                        name=f"{stage}_{metric_name}",
                        value=float(value),
                        data_type="NUMERIC",
                    )

            run_span.update(
                output={
                    "total_samples": report.total_samples,
                    "evaluated_samples": report.evaluated_samples,
                    "skipped_unanswerable_samples": (
                        report.skipped_unanswerable_samples
                    ),
                    "rrf_metrics": report.rrf_metrics,
                    "reranked_metrics": report.reranked_metrics,
                }
            )

        langfuse.flush()
        return report

    def _record_sample_scores(
            span,
            sample_id: str,
            rrf_metrics: RankingMetrics | None,
            reranked_metrics: RankingMetrics | None,
    ) -> None:
        span.update(
            metadata={
                "evaluation_sample_id": sample_id,
            }
        )

        metric_groups = {
            "rrf": rrf_metrics,
            "reranked": reranked_metrics,
        }

        for stage, metrics in metric_groups.items():
            if metrics is None:
                continue

            values = {
                "recall_at_5": metrics.recall_at_5,
                "precision_at_5": metrics.precision_at_5,
                "mrr_at_20": metrics.mrr_at_20,
                "hit_at_5": metrics.hit_at_5,
            }

            for metric_name, value in values.items():
                span.score(
                    name=f"{stage}_{metric_name}",
                    value=float(value),
                    data_type="NUMERIC",
                )

    @staticmethod
    def _aggregate_metrics(
            metrics: list[RankingMetrics | None],
    ) -> dict[str, float]:
        valid_metrics = [
            metric for metric in metrics
            if metric is not None
        ]

        if not valid_metrics:
            return {
                "recall_at_5": 0.0,
                "precision_at_5": 0.0,
                "mrr_at_20": 0.0,
                "hit_at_5": 0.0,
            }

        count = len(valid_metrics)

        return {
            "recall_at_5": sum(
                metric.recall_at_5 for metric in valid_metrics
            ) / count,
            "precision_at_5": sum(
                metric.precision_at_5 for metric in valid_metrics
            ) / count,
            "mrr_at_20": sum(
                metric.mrr_at_20 for metric in valid_metrics
            ) / count,
            "hit_at_5": sum(
                metric.hit_at_5 for metric in valid_metrics
            ) / count,
        }

    async def _rerank_with_rate_limit(
            self,
            query,
            results,
            top_k,
            request_id,
    ):
        async with self._rerank_lock:
            for attempt in range(self.max_retries + 1):
                elapsed = (
                        time.monotonic()
                        - self._last_rerank_request
                )

                wait_time = self.min_request_interval - elapsed

                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                # Record the time immediately before the API call.
                self._last_rerank_request = time.monotonic()

                try:
                    return await self.rerank(
                        query=query,
                        results=results,
                        top_k=top_k,
                        request_id=request_id,
                    )

                except TooManyRequestsError:
                    if attempt >= self.max_retries:
                        raise

                    # Wait for the rate-limit window to reset,
                    # then increase the delay on subsequent retries.
                    retry_delay = 65 * (2 ** attempt)

                    print(
                        "Cohere rate limit reached. "
                        f"Retrying in {retry_delay} seconds "
                        f"(attempt {attempt + 1}/"
                        f"{self.max_retries})."
                    )

                    await asyncio.sleep(retry_delay)
