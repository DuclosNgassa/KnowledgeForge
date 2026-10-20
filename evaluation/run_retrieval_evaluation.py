import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import UUID

from app.core.db.database import get_db, AsyncSessionLocal
from app.core.settings import settings
from app.dependencies import get_openai_embedding_provider
from evaluation.dataset import DATASET
from evaluation.retrieval_evaluator import RetrievalEvaluator
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.services.reranker.cohere_reranker import CohereReranker
from app.services.search_service import SearchService


async def run(
        search_service,
        reranker_service,
        user_id: UUID,
) -> None:
    evaluator = RetrievalEvaluator(
        hybrid_search=search_service.do_hybrid_search,
        rerank=reranker_service.rerank,
        user_id=user_id,
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
        "rrf": report.rrf_metrics,
        "reranked": report.reranked_metrics,
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
