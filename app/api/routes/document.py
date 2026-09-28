from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Request
from fastapi.params import Depends

from app.dependencies import get_current_user_info, get_document_uploader, get_ingestion_service
from app.ingestion.ingestion_service import IngestionService
from app.schemas.document import DocumentUrlRequest
from app.services.document_uploader import DocumentUploader, upload_and_save_document

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

"""
POST /documents
Content-Type: multipart/form-data

file: my-document.pdf
knowledge_base_id: optional UUID
"""


@router.post("")
async def upload_document(
        ingestion_service: Annotated[IngestionService, Depends(get_ingestion_service)],
        request: Request,
        file: UploadFile = File(...),
        knowledge_base_id: UUID | None = None,
        current_user_info: dict = Depends(get_current_user_info),
):
    user_id = current_user_info["user_id"]

    request_id = request.state.request_id

    document_id, extension, file_path, filename = await upload_and_save_document(
        file,
        request_id,
    )

    await ingestion_service.ingest(
        document_id=document_id,
        extension=extension,
        file_path=file_path,
        filename=filename,
        user_id=user_id,
        knowledge_base_id=knowledge_base_id,
    )


# TODO start the ingestion as background task


"""
POST /documents/url
Content-Type: application/json

{
    "url": "https://example.com/article",
    "knowledge_base_id": "..."
}
"""


@router.post("/url")
async def upload_from_url(
        request: DocumentUrlRequest,
        document_uploader: Annotated[DocumentUploader, Depends(get_document_uploader)],
        current_user_info: dict = Depends(get_current_user_info),
):
    user_id = current_user_info["user_id"]
    return await document_uploader.upload_from_url(
        url=str(request.url),
        user_id=user_id,
        knowledge_base_id=request.knowledge_base_id
    )
