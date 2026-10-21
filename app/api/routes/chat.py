from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_agent_service, get_chat_session_service, get_current_user_info, \
    get_chat_message_service
from app.schemas.agent_response import AgentResponse
from app.schemas.chat_request import ChatRequest
from app.schemas.chat_session_response import ChatSessionResponse, ChatMessagesResponse
from app.services.agent_service import AgentService
from app.services.chat_message_service import ChatMessageService
from app.services.chat_session_service import ChatSessionService
from fastapi.responses import StreamingResponse

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


@router.post("/sessions/{session_id}/messages/stream")
async def stream_message(
        session_id: UUID,
        chat_request: ChatRequest,
        agent_service: AgentService = Depends(get_agent_service),
        current_user_info: dict = Depends(get_current_user_info),
        chat_session_service: ChatSessionService = Depends(get_chat_session_service),
):
    chat_session = await chat_session_service.get_user_session(
        session_id=session_id,
        user_id=current_user_info["user_id"],
    )

    if chat_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        async for event in agent_service.stream_chat(
                message=chat_request.message,
                chat_session=chat_session,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ChatMessagesResponse, )
async def get_chat_messages(
        session_id: UUID,
        current_user_info: dict = Depends(get_current_user_info),
        chat_session_service: ChatSessionService = Depends(get_chat_session_service),
        chat_message_service: ChatMessageService = Depends(get_chat_message_service)
) -> ChatMessagesResponse:
    user_id = current_user_info["user_id"]
    session = await chat_session_service.get_user_session(
        session_id=session_id,
        user_id=user_id,
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = await chat_message_service.get_messages_history(session_id=session_id, limit=50)

    return ChatMessagesResponse(messages=messages)


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
        chat_session_service: ChatSessionService = Depends(get_chat_session_service),
        current_user_info: dict = Depends(get_current_user_info),
):
    session = await chat_session_service.create(
        user_id=current_user_info["user_id"]
    )

    return ChatSessionResponse(session_id=session.id)
