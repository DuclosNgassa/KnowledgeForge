import argparse
import asyncio
from uuid import UUID

from sqlalchemy import select

from app.core.db.database import AsyncSessionLocal, close_database
from app.models import DocumentChunk
from app.models.document import Document
from app.agents.agent_factory import (
    create_document_summarization_agent,
)
from app.observability.logging import logger, setup_logging

setup_logging()


async def load_document_chunks(document_id: UUID):
    async with AsyncSessionLocal() as db:
        document_result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = document_result.scalar_one_or_none()

        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        chunks_result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )

        chunks = list(chunks_result.scalars().all())

        return document.file_name, chunks


async def run(document_id: UUID):
    try:
        agent = create_document_summarization_agent()
        file_name, chunks = await load_document_chunks(document_id)

        if not chunks:
            raise ValueError(
                f"Document has no chunks: {document_id}"
            )

        logger.info("Document: %s", file_name)
        logger.info("Document ID: %s", document_id)
        logger.info("Chunks loaded: %d", len(chunks))

        source_tokens = sum(
            agent.token_counter.count(chunk.content)
            for chunk in chunks
        )

        logger.info("Source tokens: %d", source_tokens)
        logger.info(
            "Chunk range: %d - %d",
            chunks[0].chunk_index,
            chunks[-1].chunk_index,
        )

        agent = create_document_summarization_agent()
        agent.FINAL_INPUT_TOKEN_BUDGET = 1_000

        logger.info("Starting document summarization...")

        summary = await agent.summarize(chunks)

        logger.info("Summarization completed successfully.")
        logger.info("Summary length: %d characters", len(summary))

        print("\n" + "=" * 80)
        print("GENERATED DOCUMENT SUMMARY")
        print("=" * 80)
        print(summary)
        print("=" * 80)

        return summary

    finally:
        await close_database()


def main():
    parser = argparse.ArgumentParser(
        description="Run document summarization against a real database document."
    )

    parser.add_argument(
        "document_id",
        type=UUID,
        help="UUID of the document to summarize",
    )

    args = parser.parse_args()

    asyncio.run(run(args.document_id))


if __name__ == "__main__":
    main()
