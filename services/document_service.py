from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from ingestion.loader import DocumentLoader
from ingestion.upload_status import DocumentStatus
from models import Document
from repositories.document_repository import DocumentRepository

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


class DocumentService:

    def __init__(self, repository: DocumentRepository):
        self.repository = repository
        self.loader = DocumentLoader()

    async def upload_document(self,
                              file: UploadFile,
                              user_id: UUID,
                              knowledge_base_id: UUID | None = None):

        document_id, extension, file_path, filename = await _save_document_in_dir(file)

        try:
            loaded_documents = self.loader.load(str(file_path))
            # TODO create DocumentChunk objects later
            # TODO should the content be saved in db?
            # combine all pages/documents
            content = "\n\n".join(
                document.content for document in loaded_documents
            )

            print("Document content:\n", content)
            document_type = extension.lstrip(".").upper()

            document = Document(
                id=document_id,
                user_id=user_id,
                knowledge_base_id=knowledge_base_id,
                file_name=filename,
                document_type=document_type,
                source=str(file_path),
                status=DocumentStatus.COMPLETED,
            )

            return await self.repository.save(document)

        except Exception:
            # Remove file if processing fails
            file_path.unlink(missing_ok=True)
            # TODO log the error
            raise

    async def upload_from_url(self,
                              url: str,
                              user_id: UUID,
                              knowledge_base_id: UUID | None = None) -> Document:

        loaded_documents = self.loader.load(url)
        # TODO create DocumentChunk objects later
        # TODO should the content be saved in db?
        print("Loaded_documents WEB:\n", loaded_documents)
        document = Document(
            id=uuid4(),
            user_id=user_id,
            knowledge_base_id=knowledge_base_id,
            file_name=url,
            document_type="WEB",
            source=url,
            status=DocumentStatus.COMPLETED,
        )

        return await self.repository.save(document)
