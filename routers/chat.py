from fastapi import APIRouter, Depends

from auth.dependencies import AccessTokenBearer
from dependencies import get_agent_service
from schemas.agent_response import AgentResponse
from schemas.chat_request import ChatRequest
from services.agent_service import AgentService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=AgentResponse)
async def chat(
        request: ChatRequest,
        agent_service: AgentService = Depends(get_agent_service),
        token_details: dict = Depends(AccessTokenBearer())
):
    return await agent_service.chat(
        message=request.message,
    )
