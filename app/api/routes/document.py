from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Request, status, Query
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.database import get_db
from app.dependencies import get_current_user_info, get_document_uploader, get_ingestion_service, get_document_service, \
    get_document_summary_service
from app.ingestion.ingestion_service import IngestionService
from app.models.enums import DocumentStatus
from app.schemas.document import DocumentUrlRequest, UpdateDocumentKnowledgeBaseRequest, UpdateDocumentMetadataRequest
from app.schemas.document_response import DocumentResponse, DocumentListResponse, DocumentSummaryResponse
from app.services.document_service import DocumentService
from app.services.document_summary_service import DocumentSummaryService
from app.services.document_uploader import DocumentUploader, upload_and_save_document
from app.workers.document_summary_task import generate_document_summary

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


@router.post("/{document_id}/summary")
async def request_document_summary(
        document_id: UUID,
        regenerate: bool,
        db: AsyncSession = Depends(get_db),
        current_user_info: dict = Depends(get_current_user_info),
        document_summary_service: DocumentSummaryService = Depends(get_document_summary_service),
):
    summary, should_schedule = await document_summary_service.request_summary(
        document_id=document_id,
        user_id=current_user_info["user_id"],
        regenerate=regenerate,
    )
    # Ensure the summary record exists before dispatching.
    if should_schedule:
        await db.commit()

        await generate_document_summary.kiq(
            document_id_str=str(document_id),
        )

    return summary


@router.get("/{document_id}/summary",
            response_model=DocumentSummaryResponse,
            status_code=status.HTTP_200_OK)
async def get_document_summary(
        document_id: UUID,
        current_user_info: dict = Depends(get_current_user_info),
        document_summary_service: DocumentSummaryService = Depends(get_document_summary_service),
) -> DocumentSummaryResponse:
    document_summary = await document_summary_service.get_summary(
        document_id=document_id,
        user_id=current_user_info["user_id"],
    )

    return DocumentSummaryResponse.model_validate(document_summary)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
        document_id: UUID,
        current_user_info: dict = Depends(get_current_user_info),
        document_service: DocumentService = Depends(get_document_service),
):
    await document_service.delete_document(
        document_id=document_id,
        user_id=current_user_info["user_id"],
    )
