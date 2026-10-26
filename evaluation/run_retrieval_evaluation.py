import asyncio

from langchain_openai import ChatOpenAI

from app.services.citation_grounding_service import CitationGroundingService
from app.services.citation_service import CitationService

def debug_asyncio_run(stage: str) -> None:
    print(
        f"[{stage}] asyncio.run = "
        f"{asyncio.run.__module__}.{asyncio.run.__name__}"
    )


import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import UUID

from app.core.db.database import AsyncSessionLocal
from app.core.settings import settings
from app.dependencies import get_openai_embedding_provider

from evaluation.dataset import DATASET

debug_asyncio_run("after dataset import")
from evaluation.rag_quality_evaluator import RagQualityEvaluator

debug_asyncio_run("after rag quality evaluator import")

from evaluation.retrieval_evaluator import RetrievalEvaluator

debug_asyncio_run("after retrieval evaluator import")
from app.repositories.document_chunk_repository import DocumentChunkRepository

debug_asyncio_run("after DocumentChunkRepository import")
from app.services.reranker.cohere_reranker import CohereReranker
from app.services.search_service import SearchService
from app.services.answer_generator import AnswerGenerator

debug_asyncio_run("after evaluation imports")


async def run(
        search_service,
        reranker_service,
        user_id: UUID,
) -> None:
    llm = ChatOpenAI(
        model=settings.openai_chat_model,
    )

    answer_generator = AnswerGenerator(llm=llm)
    citation_service = CitationService()
    citation_grounding_service = CitationGroundingService(citation_service)
    rag_quality_evaluator = RagQualityEvaluator(citation_grounding_service)


    evaluator = RetrievalEvaluator(
        hybrid_search=search_service.do_hybrid_search,
        rerank=reranker_service.rerank,
        user_id=user_id,
        rag_quality_evaluator=rag_quality_evaluator,
        answer_generator=answer_generator,
        citation_service=citation_service,
        candidate_k=20,
        final_k=5,
    )

    samples = DATASET
    report = await evaluator.evaluate(samples)

    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_path = results_dir / f"retrieval_results_{timestamp}.json"

    output_path.write_text(
        json.dumps(asdict(report), indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "samples": report.total_samples,
        "evaluated": report.evaluated_samples,
        "skipped_unanswerable": (
            report.skipped_unanswerable_samples
        ),
        "retrieval_quality": report.retrieval_metrics,
        "answer_quality": report.answer_quality_metrics,
        "citation_quality": report.citation_quality_metrics,
        "output": str(output_path),
    }, indent=2))


async def main() -> None:
    user_id = UUID(
        "c1271fdd-8096-4a49-8a9d-5f551cac576e"
    )

    embedding_provider = get_openai_embedding_provider()
    reranker_service = CohereReranker(
        api_key=settings.cohere_api_key
    )

    async with AsyncSessionLocal() as session:
        search_service = SearchService(
            document_chunk_repository=DocumentChunkRepository(
                session
            ),
            embedding_provider=embedding_provider,
        )

        await run(
            search_service,
            reranker_service,
            user_id,
        )


if __name__ == "__main__":
    asyncio.run(main())
