from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Request, status, Query
from fastapi.params import Depends

from app.dependencies import get_current_user_info, get_document_uploader, get_ingestion_service, get_document_service
from app.ingestion.ingestion_service import IngestionService
from app.ingestion.models.document_status import DocumentStatus
from app.schemas.document import DocumentUrlRequest, UpdateDocumentKnowledgeBaseRequest, UpdateDocumentMetadataRequest
from app.schemas.document_response import DocumentResponse, DocumentListResponse
from app.services.document_service import DocumentService
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


@router.post("", response_model=DocumentResponse, status_code=201)
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

    document = await ingestion_service.ingest(
        document_id=document_id,
        extension=extension,
        file_path=file_path,
        filename=filename,
        user_id=user_id,
        knowledge_base_id=knowledge_base_id,
    )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=DocumentListResponse, status_code=200)
async def get_documents(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: DocumentStatus | None = None,
        document_type: str | None = None,
        sort_order: Literal["asc", "desc"] = "desc",
        current_user_info: dict = Depends(get_current_user_info),
        document_service: DocumentService = Depends(get_document_service),
):
    user_id = current_user_info["user_id"]
    return await document_service.find_all(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        document_type=document_type,
        sort_order=sort_order,
    )


@router.get(
    "/knowledge-bases/{knowledge_base_id}",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
)
async def find_all_by_knowledge_base_id(
        knowledge_base_id: UUID,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: DocumentStatus | None = None,
        document_type: str | None = None,
        sort_order: Literal["asc", "desc"] = "desc",
        current_user_info: dict = Depends(get_current_user_info),
        document_service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    user_id = current_user_info["user_id"]
    return await document_service.get_documents_by_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        document_type=document_type,
        sort_order=sort_order,
    )


@router.patch(
    "/{document_id}/knowledge-base",
    response_model=DocumentResponse,
    status_code=201
)
async def update_document_knowledge_base(
        document_id: UUID,
        request: UpdateDocumentKnowledgeBaseRequest,
        current_user_info: dict = Depends(get_current_user_info),
        document_service: DocumentService = Depends(get_document_service),
):
    return await document_service.update_knowledge_base(
        document_id=document_id,
        user_id=current_user_info["user_id"],
        knowledge_base_id=request.knowledge_base_id
    )


@router.patch(
    "/{document_id}/metadata",
    response_model=DocumentResponse,
    status_code=201
)
async def update_document_metadata(
        document_id: UUID,
        request: UpdateDocumentMetadataRequest,
        current_user_info: dict = Depends(get_current_user_info),
        document_service: DocumentService = Depends(get_document_service),
):
    return await document_service.update_metadata(
        document_id=document_id,
        user_id=current_user_info["user_id"],
        request=request,
    )


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
