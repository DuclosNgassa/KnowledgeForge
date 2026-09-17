from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from fastapi.params import Depends

from dependencies import get_embedding_service
from services.embedding_service import EmbeddingService

router = APIRouter(
    prefix="/embeddings",
    tags=["Embeddings"],
)


# TODO This endpoint is exclusively for development purposes
@router.post("/process",
             status_code=status.HTTP_202_ACCEPTED, )
async def process_embeddings(embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
                             document_id: UUID | None = None):
    processed = await embedding_service.process_pending_chunks(document_id=document_id)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "processed": processed,
        }
    )
