from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, UploadFile, File
from fastapi.params import Depends

from dependencies import get_current_user_info, get_document_service
from schemas.document import DocumentUrlRequest
from services.document_service import DocumentService

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
        service: Annotated[DocumentService, Depends(get_document_service)],
        file: UploadFile = File(...),
        knowledge_base_id: UUID | None = None,
        current_user_info: dict = Depends(get_current_user_info),
):
    user_id = current_user_info["user_id"]
    return await service.upload_document(
        file,
        user_id,
        knowledge_base_id)


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
        service: Annotated[DocumentService, Depends(get_document_service)],
        current_user_info: dict = Depends(get_current_user_info),
):
    user_id = current_user_info["user_id"]
    return await service.upload_from_url(
        url=str(request.url),
        user_id=user_id,
        knowledge_base_id=request.knowledge_base_id
    )
