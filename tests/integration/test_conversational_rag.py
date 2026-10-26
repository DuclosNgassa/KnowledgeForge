import asyncio
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.tools.document_search import create_search_documents_tool
from app.services.conversation_context import ConversationContext

"""
What these tests verify
Test	Expected result
Follow-up question:	"How many days do I get?" is contextualized using the vacation-policy history.
Hybrid search:	Receives the rewritten query, not the original follow-up.
Reranking:	Receives exactly the same rewritten query as hybrid search.
Concurrent conversations:	Vacation and expense histories produce distinct queries when invoked concurrently.

Important limitation: the concurrency test constructs separate contexts and separate tool dependencies, matching 
the request-scoped design we want. It verifies the tool integration, but it does not yet exercise FastAPI request 
handling or the full AgentService.stream_chat() lifecycle.
"""


class FakeQueryContextualizer:
    """Deterministically rewrite questions using the supplied history."""

    async def contextualize(self, question, history):
        history_text = " ".join(
            str(message.content) for message in history
        ).lower()

        if "vacation policy" in history_text:
            return f"vacation policy: {question}"

        if "expense policy" in history_text:
            return f"expense policy: {question}"

        return question


def make_search_result(document_id: str, content: str):
    return SimpleNamespace(
        chunk_id=str(uuid4()),
        document_id=document_id,
        content=content,
        file_name=f"{document_id}.pdf",
        page_number=1,
        source=document_id,
        score=0.9,
    )


def make_context(*messages):
    context = ConversationContext()
    context.set_history(list(messages))
    return context


@pytest.mark.asyncio
async def test_follow_up_question_uses_contextualized_query():
    user_id = uuid4()
    query_contextualizer = FakeQueryContextualizer()

    search_service = SimpleNamespace(
        do_hybrid_search=AsyncMock(
            return_value=[
                make_search_result("vacation-handbook", "Annual leave policy")
            ]
        )
    )
    reranker = SimpleNamespace(
        rerank=AsyncMock(
            side_effect=lambda query, results, **kwargs: results
        )
    )

    context = make_context(
        HumanMessage(content="Tell me about the vacation policy."),
        AIMessage(content="The handbook describes annual leave."),
    )

    search_tool = create_search_documents_tool(
        search_service=search_service,
        reranker=reranker,
        user_id=user_id,
        query_contextualizer=query_contextualizer,
        conversation_context=context,
    )

    await search_tool.ainvoke({"query": "How many days do I get?"})

    expected_query = "vacation policy: How many days do I get?"

    search_service.do_hybrid_search.assert_awaited_once_with(
        query=expected_query,
        user_id=user_id,
        limit=5,
        request_id=None,
    )

    reranker.rerank.assert_awaited_once()

    reranker_query = reranker.rerank.await_args.kwargs["query"]
    assert reranker_query == expected_query


@pytest.mark.asyncio
async def test_concurrent_conversations_do_not_mix_history():
    user_id = uuid4()
    query_contextualizer = FakeQueryContextualizer()

    vacation_search = SimpleNamespace(
        do_hybrid_search=AsyncMock(
            return_value=[
                make_search_result("vacation-handbook", "Vacation information")
            ]
        )
    )
    expense_search = SimpleNamespace(
        do_hybrid_search=AsyncMock(
            return_value=[
                make_search_result("expense-handbook", "Expense information")
            ]
        )
    )

    vacation_reranker = SimpleNamespace(
        rerank=AsyncMock(side_effect=lambda query, results, **kwargs: results)
    )
    expense_reranker = SimpleNamespace(
        rerank=AsyncMock(side_effect=lambda query, results, **kwargs: results)
    )

    vacation_context = make_context(
        HumanMessage(content="Tell me about the vacation policy.")
    )
    expense_context = make_context(
        HumanMessage(content="Tell me about the expense policy.")
    )

    vacation_tool = create_search_documents_tool(
        search_service=vacation_search,
        reranker=vacation_reranker,
        user_id=user_id,
        query_contextualizer=query_contextualizer,
        conversation_context=vacation_context,
    )
    expense_tool = create_search_documents_tool(
        search_service=expense_search,
        reranker=expense_reranker,
        user_id=user_id,
        query_contextualizer=query_contextualizer,
        conversation_context=expense_context,
    )

    await asyncio.gather(
        vacation_tool.ainvoke({"query": "What are the rules?"}),
        expense_tool.ainvoke({"query": "What are the rules?"}),
    )

    vacation_search.do_hybrid_search.assert_awaited_once_with(
        query="vacation policy: What are the rules?",
        user_id=user_id,
        limit=5,
        request_id=None,
    )
    expense_search.do_hybrid_search.assert_awaited_once_with(
        query="expense policy: What are the rules?",
        user_id=user_id,
        limit=5,
        request_id=None,
    )

    assert (
            vacation_reranker.rerank.await_args.kwargs["query"]
            == "vacation policy: What are the rules?"
    )
    assert (
            expense_reranker.rerank.await_args.kwargs["query"]
            == "expense policy: What are the rules?"
    )
