import uuid
from typing import Annotated
from uuid import UUID
from fastapi.responses import JSONResponse

from fastapi import APIRouter, Depends, status

from auth.dependencies import AccessTokenBearer
from dependencies import get_knowledge_base_service, get_current_user_info
from schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseResponse, KnowledgeBaseUpdate, \
    KnowledgeBaseListResponse
from services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(
    prefix="/knowledge-bases",
    tags=["Knowledge Bases"],
)


@router.post(
    "",
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


@router.put(
    "/{knowledge_base_id}",
    response_model=KnowledgeBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def update_knowledge_base(
        knowledge_base_id: uuid.UUID,
        data: KnowledgeBaseUpdate,
        service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
        current_user_info: dict = Depends(get_current_user_info),
) -> KnowledgeBaseResponse:
    print("current_user_info in knowledge_base: ", current_user_info)
    user_id = current_user_info["user_id"]
    result = await service.update_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        data=data,
        user_id=user_id,
    )

    return KnowledgeBaseResponse.model_validate(result)


@router.get(
    "",
    response_model=KnowledgeBaseListResponse,
    status_code=status.HTTP_200_OK,
)
async def find_all(
        service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
        user_detail: dict = Depends(get_current_user_info),
) -> KnowledgeBaseListResponse:
    user_id = user_detail["user_id"]
    return await service.find_all(user_id)


@router.delete(
    "/{knowledge_base_id}",
    response_model=str,
    status_code=status.HTTP_200_OK)
async def delete(knowledge_base_id: UUID,
                 service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
                 current_user_info: dict = Depends(get_current_user_info),
                 ) -> JSONResponse:
    user_id = current_user_info["user_id"]
    await service.delete(knowledge_base_id=knowledge_base_id, user_id=user_id)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Knowledge Base deleted successfully. [id: {knowledge_base_id}]",
        }
    )
