from typing import Annotated

from fastapi import APIRouter, Depends, status

from auth.dependencies import AccessTokenBearer
from dependencies import get_knowledge_base_service
from schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse
from services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["Knowledge Bases"],
)


@router.post(
    "/create",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
        data: KnowledgeBaseCreate,
        service: Annotated[
            KnowledgeBaseService, Depends(get_knowledge_base_service)
        ],
        token_details: dict = Depends(AccessTokenBearer()),
) -> KnowledgeBaseResponse:
    print("token_details in knowledge_base: ", token_details)

    current_user_id = token_details["user"]["user_id"]

    knowledge_base = await service.create_knowledge_base(
        data=data,
        user_id=current_user_id,
    )

    return KnowledgeBaseResponse.model_validate(knowledge_base)
