import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from evaluation.rag_quality_evaluator import RagQualityEvaluator
from evaluation.schemas import EvaluationSample
from evaluation.metrics import expected_chunk_ids
import time
from cohere.errors import TooManyRequestsError

from app.observability.langfuse import langfuse
from app.services.answer_generator import AnswerGenerator
from app.observability.logging import logger
from app.schemas.retrieved_document import RetrievedDocument
from app.services.citation_service import CitationService


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
    rag_score: dict[str, float]
    grounding: dict | None = None


@dataclass
class RetrievalReport:
    total_samples: int
    evaluated_samples: int
    skipped_unanswerable_samples: int

    retrieval_metrics: dict
    answer_quality_metrics: dict
    citation_quality_metrics: dict

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
            answer_generator: AnswerGenerator,
            citation_service: CitationService,
            rag_quality_evaluator: RagQualityEvaluator,
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
        self.answer_generator = answer_generator
        self.citation_service = citation_service
        self.rag_quality_evaluator = rag_quality_evaluator
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
            # Retrieve candidates using hybrid search
            candidates = await self.hybrid_search(
                query=sample["question"],
                user_id=self.user_id,
                limit=self.candidate_k,
            )

            rrf_ids = self._chunk_ids(candidates)

            # Rerank candidates
            reranked_results = await self._rerank_with_rate_limit(
                query=sample["question"],
                results=candidates,
                top_k=self.candidate_k,
                request_id=f"eval-{sample['id']}",
            )

            # Build the citation registry from the retrieved evidence used as context.
            grounding_results = [
                result
                for result in reranked_results[:5]
                if result.content and result.content.strip()
            ]

            contexts = [result.content for result in grounding_results]

            # Generate an answer for both answerable and unanswerable questions
            answer = await self.answer_generator.generate_answer(
                question=sample["question"],
                contexts=contexts,
            )

            logger.info("Generated evaluation answer: %s", answer)
            logger.info(
                "Extracted answer citations: %s",
                self.citation_service.extract_citations(answer),
            )

            documents = [
                RetrievedDocument(
                    chunk_id=str(result.chunk_id),
                    document_id=str(result.document_id),
                    content=result.content,
                    filename=result.file_name,
                    page_number=result.page_number,
                )
                for result in grounding_results
            ]

            registry = self.citation_service.build_registry(
                documents=documents,
                web_results=[],
            )

            grounding_report = (
                await self.rag_quality_evaluator.evaluate_citation_grounding(
                    answer=answer,
                    registry=registry,
                )
            )

            grounding = grounding_report.model_dump(mode="json")

            # Unanswerable questions are handled separately.
            if not sample["answerable"]:
                rag_score = await self.rag_quality_evaluator.evaluate_unanswerable(
                    question=sample["question"],
                    answer=answer,
                    contexts=contexts,
                )
                span.score(
                    name="abstention_correctness",
                    value=rag_score["abstention_correctness"],
                    data_type="NUMERIC",
                )

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
                    rag_score=rag_score,
                    grounding=grounding,
                )

            rag_score = await self.rag_quality_evaluator.evaluate(
                question=sample["question"],
                answer=answer,
                contexts=contexts,
            )

            span.score(
                name="faithfulness",
                value=rag_score["faithfulness"],
                data_type="NUMERIC",
            )
            span.score(
                name="answer_relevancy",
                value=rag_score["answer_relevancy"],
                data_type="NUMERIC",
            )
            span.score(
                name="grounded_claim_ratio",
                value=grounding_report.grounded_claim_ratio or 0.0,
                data_type="NUMERIC",
            ) if grounding_report.grounded_claim_ratio is not None else None

            relevant_ids = expected_chunk_ids(sample)

            rrf_metrics = calculate_metrics(
                relevant_ids,
                rrf_ids,
                self.final_k,
            )

            reranked_ids = self._chunk_ids(reranked_results)

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
                    "citation_grounding": grounding_report.model_dump(mode="json")
                }
            )

            return SampleRetrievalResult(
                sample_id=sample["id"],
                question_type=sample["question_type"],
                difficulty=sample["difficulty"],
                answerable=True,
                rrf=rrf_metrics,
                reranked=reranked_metrics,
                rag_score=rag_score,
                grounding=grounding
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

            # Retrieval metrics require answerable samples
            # with known relevant chunks.
            retrieval_samples = [
                result for result in results
                if result.answerable
            ]

            rrf_metrics = self._aggregate_metrics(
                [result.rrf for result in retrieval_samples]
            )

            reranked_metrics = self._aggregate_metrics(
                [result.reranked for result in retrieval_samples]
            )

            retrieval_metrics = {
                "rrf": rrf_metrics,
                "reranked": reranked_metrics,
            }

            # Answer-quality metrics: evaluate answerable samples
            # for which RAGAS scores are available.
            answer_samples = [
                result for result in results
                if result.answerable
                   and result.rag_score is not None
            ]

            answer_quality_metrics = self._aggregate_rag_metrics(
                [result.rag_score for result in answer_samples]
            )

            # Citation quality can include any sample with a
            # grounding report, including unanswerable questions.
            citation_samples = [
                result for result in results
                if result.grounding is not None
            ]

            citation_quality_metrics = (
                self._aggregate_grounding_metrics(
                    [result.grounding for result in citation_samples]
                )
            )

            # Record each group with a distinct prefix in Langfuse.
            for method, metrics in retrieval_metrics.items():
                self._record_metric_group(
                    run_span,
                    f"retrieval_{method}",
                    metrics,
                )

            self._record_metric_group(
                run_span,
                "answer",
                answer_quality_metrics,
            )

            self._record_metric_group(
                run_span,
                "citation",
                citation_quality_metrics,
            )

            report = RetrievalReport(
                total_samples=len(samples),
                evaluated_samples=len(results),
                skipped_unanswerable_samples=(
                        len(results) - len(retrieval_samples)
                ),
                retrieval_metrics=retrieval_metrics,
                answer_quality_metrics=answer_quality_metrics,
                citation_quality_metrics=citation_quality_metrics,
                results=results,
            )

            run_span.update(
                output={
                    "total_samples": len(samples),
                    "evaluated_samples": len(results),
                    "answerable_samples_used_for_retrieval": (
                        len(retrieval_samples)
                    ),
                    "samples_used_for_answer_quality": len(answer_samples),
                    "samples_used_for_citation_quality": len(citation_samples),
                    "retrieval_metrics": retrieval_metrics,
                    "answer_quality_metrics": answer_quality_metrics,
                    "citation_quality_metrics": citation_quality_metrics,
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
    def _record_metric_group(
            observation,
            prefix: str,
            metrics: dict,
    ) -> None:
        for metric_name, value in metrics.items():
            if value is None or isinstance(value, bool):
                continue

            if not isinstance(value, (int, float)):
                continue

            observation.score(
                name=f"{prefix}_{metric_name}",
                value=value,
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

    @staticmethod
    def _aggregate_rag_metrics(
            scores: list[dict[str, float] | None],
    ) -> dict[str, float | None]:
        metric_names = (
            "faithfulness",
            "answer_relevancy",
            "abstention_correctness",
        )

        result: dict[str, float | None] = {}

        for metric in metric_names:
            values = [
                value
                for score in scores
                if score is not None
                if (value := score.get(metric)) is not None
            ]

            result[metric] = (
                sum(values) / len(values)
                if values
                else None
            )

        return result

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

    def _aggregate_grounding_metrics(
            self,
            grounding_reports: list[dict | None],
    ) -> dict[str, float | int | None]:
        total_claims = 0
        supported_claims = 0
        cited_claims = 0
        supported_cited_claims = 0

        for report in grounding_reports:
            if report is None:
                continue

            claims = report.get("claims", [])

            for claim in claims:
                total_claims += 1

                is_supported = claim["supported"]
                has_citation = bool(claim.get("citation_ids", []))

                if is_supported:
                    supported_claims += 1

                if has_citation:
                    cited_claims += 1

                    if is_supported:
                        supported_cited_claims += 1

        return {
            "total_claims": total_claims,
            "supported_claims": supported_claims,
            "cited_claims": cited_claims,
            "supported_cited_claims": supported_cited_claims,
            "grounded_claim_ratio": (
                supported_claims / total_claims
                if total_claims > 0
                else None
            ),
            "citation_coverage": (
                cited_claims / total_claims
                if total_claims > 0
                else None
            ),
            "citation_support_rate": (
                supported_cited_claims / cited_claims
                if cited_claims > 0
                else None
            ),
        }
