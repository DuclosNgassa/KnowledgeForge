from fastapi import APIRouter, Depends

from app.auth.dependencies import AccessTokenBearer
from app.dependencies import get_agent_service
from app.schemas.agent_response import AgentResponse
from app.schemas.chat_request import ChatRequest
from app.services.agent_service import AgentService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=AgentResponse)
async def chat(
        chat_request: ChatRequest,
        agent_service: AgentService = Depends(get_agent_service),
        token_details: dict = Depends(AccessTokenBearer())
):

    return await agent_service.chat(
        message=chat_request.message,
    )
