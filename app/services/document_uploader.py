from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from app.ingestion.loaders.loader import DocumentLoader
from app.ingestion.models.document_status import DocumentStatus
from app.ingestion.models.loaded_document import LoadedDocument
from app.models import Document

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


async def upload_and_save_document(file: UploadFile, request_id: UUID | None = None) -> tuple[UUID, str, Path, str]:
    # 1. Save document in dir
    return await _save_document_in_dir(file)


class DocumentUploader:

    def __init__(self, document_loader: DocumentLoader, ):
        self.document_loader = document_loader

    async def upload_from_url(self,
                              url: str,
                              user_id: UUID,
                              knowledge_base_id: UUID | None = None,
                              ) -> tuple[Document, list[LoadedDocument]]:
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

        return document, loaded_documents
