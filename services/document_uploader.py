from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.embedding_status import EmbeddingStatus
from ingestion.loader import DocumentLoader
from ingestion.document_status import DocumentStatus
from models import Document, DocumentChunk
from repositories.document_chunk_repository import DocumentChunkRepository
from repositories.document_repository import DocumentRepository
from schemas.document_chunk import DocumentChunkData
from services.document_chunker import DocumentChunkService

UPLOAD_DIR = Path("uploads/documents")


async def _save_document_in_dir(file: UploadFile) -> tuple[UUID, str, Path, str]:
    if not file.filename:
        raise ValueError("Filename is required")

    extension = Path(file.filename).suffix.lower()

    supported_extensions = [".pdf", ".docx", ".md", ".txt"]

    if extension not in supported_extensions:
        raise ValueError(f"File extension {extension} not supported. Supported extensions: {supported_extensions}")

    document_id = uuid4()

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    file_path = UPLOAD_DIR / f"{document_id}{extension}"

    # Save uploaded file
    with file_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)
    return document_id, extension, file_path, file.filename


class DocumentUploader:

    def __init__(self,
                 repository: DocumentRepository,
                 document_chunk_service: DocumentChunkService,
                 document_chunk_repository: DocumentChunkRepository,
                 document_loader: DocumentLoader,
                 session: AsyncSession):

        self.document_repository = repository
        self.document_chunk_service = document_chunk_service
        self.document_chunk_repository = document_chunk_repository
        self.document_loader = document_loader
        self.session = session

    async def upload_document(self,
                              file: UploadFile,
                              user_id: UUID,
                              knowledge_base_id: UUID | None = None):

        # 1. Save document in dir
        document_id, extension, file_path, filename = await _save_document_in_dir(file)

        try:
            # 2. Extract content from dir
            loaded_documents = self.document_loader.load(str(file_path))

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
            await self.document_repository.save(document)

            # 5. Chunk
            chunks: list[DocumentChunkData] = self.document_chunk_service.chunk(loaded_documents)

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
            await self.document_chunk_repository.save_all(document_chunks)

            # 8. Mark Ingestion as completed
            document.status = DocumentStatus.COMPLETED

            # 9. Commit entire transaction
            await self.session.commit()

            return document

        except Exception:
            await self.session.rollback()

            # Remove file if processing fails
            file_path.unlink(missing_ok=True)
            # TODO log the error
            raise

    async def upload_from_url(self,
                              url: str,
                              user_id: UUID,
                              knowledge_base_id: UUID | None = None) -> Document:

        loaded_documents = self.document_loader.load(url)
        # TODO create DocumentChunk objects later
        # TODO should the content be saved in db?
        document = Document(
            id=uuid4(),
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            file_name=url,
            document_type="WEB",
            source=url,
            status=DocumentStatus.COMPLETED,
        )

        return await self.document_repository.save(document)
