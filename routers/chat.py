from fastapi import APIRouter, Depends

from auth.dependencies import AccessTokenBearer
from dependencies import get_agent_service
from schemas.chat_request import ChatRequest
from services.agent_service import AgentService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("")
async def chat(
        request: ChatRequest,
        agent_service: AgentService = Depends(get_agent_service),
        token_details: dict = Depends(AccessTokenBearer())
):
    answer = await agent_service.chat(
        message=request.message,
    )
    return {
        "answer": answer,
    }
