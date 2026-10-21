import json
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from langfuse._client.propagation import propagate_attributes
from langfuse.langchain import CallbackHandler

from app.models import ChatSession
from app.models.chat_message import MessageRole
from app.observability.langfuse import langfuse
from app.observability.logging import logger
from app.schemas.agent_response import AgentResponse
from app.services.chat_message_service import (
    ChatMessageService,
    to_langchain_message,
)

MAX_HISTORY_MESSAGES = 20


def sse_event(event: str, data: dict[str, Any]) -> str:
    """Format a JSON payload as a Server-Sent Event."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


class AgentService:
    def __init__(
            self,
            agent,
            chat_message_service: ChatMessageService,
            streaming_model,
    ):
        self.agent = agent
        self.chat_message_service = chat_message_service
        self.streaming_model = streaming_model

    async def chat(self,
                   message: str,
                   chat_session: ChatSession,
                   ) -> AgentResponse:
        history = await self.chat_message_service.get_messages_history(
            session_id=chat_session.id,
            limit=MAX_HISTORY_MESSAGES,
        )
        messages = to_langchain_message(history)

        messages.append(HumanMessage(content=message))

        langfuse_handler = CallbackHandler()

        with langfuse.start_as_current_observation(
                as_type="agent",
                name="agent-chat",
                input={
                    "message": message,
                }
        ) as agent_observation:
            with propagate_attributes(
                    session_id=str(chat_session.id),
                    user_id=str(chat_session.user_id),
            ):
                for index, msg in enumerate(messages):
                    logger.info(
                        "Agent input [%d] %s: %s",
                        index,
                        type(msg).__name__,
                        str(msg.content)[:300],
                    )

                response = await self.agent.ainvoke(
                    {
                        "messages": messages
                    },
                    config={
                        "callbacks": [langfuse_handler],
                    }
                )
            # TODO better handling of none agent_response
            logger.info("Agent response keys: %s", response.keys())
            logger.info("Full agent response: %r", response)

            agent_response = response.get("structured_response")

            if agent_response is None:
                raise RuntimeError(
                    "Agent did not return structured_response. "
                    f"Available keys: {list(response.keys())}"
                )

            agent_response = response["structured_response"]

            agent_observation.update(
                output={
                    "answer": agent_response.answer,
                    "sources": [
                        source.model_dump(mode="json")
                        for source in agent_response.sources
                    ],
                }
            )

        # persist conversation
        await self.chat_message_service.add_message(
            session_id=chat_session.id,
            role=MessageRole.USER,
            content=message,
        )

        await self.chat_message_service.add_message(
            session_id=chat_session.id,
            role=MessageRole.ASSISTANT,
            content=agent_response.answer,
        )

        return agent_response

    async def stream_chat(
            self,
            message: str,
            chat_session: ChatSession,
    ) -> AsyncIterator[str]:
        history = await self.chat_message_service.get_messages_history(
            session_id=chat_session.id,
            limit=MAX_HISTORY_MESSAGES,
        )

        messages = to_langchain_message(history)
        messages.append(HumanMessage(content=message))

        langfuse_handler = CallbackHandler()

        try:
            with langfuse.start_as_current_observation(
                    as_type="agent",
                    name="agent-chat-stream",
                    input={"message": message},
            ) as observation:
                with propagate_attributes(
                        session_id=str(chat_session.id),
                        user_id=str(chat_session.user_id),
                ):
                    # Phase 1: retrieve information and identify sources.
                    agent_result = await self.agent.ainvoke(
                        {"messages": messages},
                        config={"callbacks": [langfuse_handler]},
                    )

                    agent_response = agent_result.get("structured_response")

                    if agent_response is None:
                        raise RuntimeError(
                            "The agent did not return a structured response."
                        )

                    if not isinstance(agent_response, AgentResponse):
                        agent_response = AgentResponse.model_validate(
                            agent_response
                        )

                    # Tell the client that retrieval is finished.
                    yield sse_event("sources", {
                        "sources": [
                            source.model_dump(mode="json")
                            for source in agent_response.sources
                        ],
                        "web_sources": [
                            source.model_dump(mode="json")
                            if hasattr(source, "model_dump")
                            else source
                            for source in agent_response.web_sources
                        ],
                    })

                    # Phase 2: stream the final answer.
                    # This second call is necessary because the agent's
                    # structured AgentResponse is returned as a tool call.
                    stream_messages = [
                        SystemMessage(
                            content=(
                                "Produce the final answer using only the "
                                "information in the supplied draft answer. "
                                "Preserve its factual meaning. Do not invent "
                                "facts, sources, or citations. Return only "
                                "the answer text, without commentary about "
                                "the draft."
                            )
                        ),
                        HumanMessage(
                            content=(
                                "Draft answer:\n"
                                f"{agent_response.answer}"
                            )
                        ),
                    ]

                    answer_parts: list[str] = []

                    async for chunk in self.streaming_model.astream(
                            stream_messages
                    ):
                        content = chunk.content

                        # Gemini can return either a string or structured
                        # content blocks. Only emit actual text.
                        if isinstance(content, str):
                            text = content
                        elif isinstance(content, list):
                            text = "".join(
                                block.get("text", "")
                                for block in content
                                if isinstance(block, dict)
                                and block.get("type") == "text"
                            )
                        else:
                            text = ""

                        if not text:
                            continue

                        answer_parts.append(text)
                        yield sse_event("token", {"text": text})

                    final_answer = "".join(answer_parts).strip()

                    # Persist only after successful generation.
                    await self.chat_message_service.add_message(
                        session_id=chat_session.id,
                        role=MessageRole.USER,
                        content=message,
                    )
                    await self.chat_message_service.add_message(
                        session_id=chat_session.id,
                        role=MessageRole.ASSISTANT,
                        content=final_answer,
                    )

                    observation.update(output={
                        "answer": final_answer,
                        "sources": [
                            source.model_dump(mode="json")
                            for source in agent_response.sources
                        ],
                    })

                    yield sse_event("done", {
                        "answer": final_answer,
                        "sources": [
                            source.model_dump(mode="json")
                            for source in agent_response.sources
                        ],
                        "web_sources": [
                            source.model_dump(mode="json")
                            if hasattr(source, "model_dump")
                            else source
                            for source in agent_response.web_sources
                        ],
                    })

        except Exception:
            logger.exception("Streaming chat failed")
            yield sse_event("error", {
                "message": "The response could not be generated."
            })
