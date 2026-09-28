from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.chunker.document_chunker import DocumentChunkService
from app.ingestion.loaders.loader import DocumentLoader
from app.ingestion.models.document_status import DocumentStatus
from app.ingestion.models.embedding_status import EmbeddingStatus
from app.models import Document, DocumentChunk
from app.schemas.document_chunk import DocumentChunkData
from app.services.document_service import DocumentService


class IngestionService:

    def __init__(self,
                 loader: DocumentLoader,
                 chunker: DocumentChunkService,
                 document_service: DocumentService,
                 session: AsyncSession,
                 ):
        self.loader = loader
        self.chunker = chunker
        self.document_service = document_service
        self.session = session

    async def ingest(self,
                     document_id,
                     extension,
                     file_path,
                     filename,
                     user_id: UUID,
                     knowledge_base_id: UUID | None = None,
                     ):
        try:
            # 2. Extract content from dir
            loaded_documents = self.loader.load(str(file_path))

            document_type = extension.lstrip(".").upper()

            # 3. Create Document
            document = Document(
                id=document_id,
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                file_name=filename,
                document_type=document_type,
                source=str(file_path),
                status=DocumentStatus.PROCESSING,
            )

            # 4. Save the document with flush to make document_id available
            await self.document_service.save(document)

            # 5. Chunk
            chunks: list[DocumentChunkData] = self.chunker.chunk(loaded_documents)

            # 6. Create DocumentChunk entities
            document_chunks = [
                DocumentChunk(
                    document_id=document.id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.metadata.get("page", 0) + 1,
                    metadata_chunk=chunk.metadata,
                    embedding_status=EmbeddingStatus.PENDING,
                )
                for chunk in chunks
            ]

            # 7. Save chunks
            await self.chunker.save_all(document_chunks)

            # 8. Mark Ingestion as completed
            document.status = DocumentStatus.COMPLETED

            # 9. Commit entire transaction
            await self.session.commit()

            # 10. TODO run embedding as job in background
            return document

        except Exception:
            await self.session.rollback()

            # Remove file if processing fails
            file_path.unlink(missing_ok=True)
            # TODO log the error
            raise
