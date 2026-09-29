from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_agent_service, get_chat_session_service, get_current_user_info
from app.schemas.agent_response import AgentResponse
from app.schemas.chat_request import ChatRequest
from app.schemas.chat_session_response import ChatSessionResponse
from app.services.agent_service import AgentService
from app.services.chat_session_service import ChatSessionService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=AgentResponse,
)
async def chat(
        session_id: UUID,
        chat_request: ChatRequest,
        agent_service: AgentService = Depends(get_agent_service),
        current_user_info: dict = Depends(get_current_user_info),
        chat_session_service: ChatSessionService = Depends(get_chat_session_service),
):
    chat_session = await chat_session_service.get_user_session(
        session_id=session_id,
        user_id=current_user_info["user_id"]
    )

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return await agent_service.chat(
        message=chat_request.message,
        chat_session=chat_session,
    )


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
        chat_session_service: ChatSessionService = Depends(get_chat_session_service),
        current_user_info: dict = Depends(get_current_user_info),
):
    session = await chat_session_service.create(
        user_id=current_user_info["user_id"]
    )

    return ChatSessionResponse(session_id=session.id)
