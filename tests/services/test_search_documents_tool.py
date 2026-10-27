from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.services.conversation_context import ConversationContext
from app.services.query_contextualizer import QueryContextualizer

from app.agents.tools.document_search import create_search_documents_tool


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def conversation_context():
    context = ConversationContext()
    context.set_history(
        history=[
            HumanMessage(
                content="What does our employee handbook say about parental leave?"
            ),
            AIMessage(
                content="It describes eligibility and the application process."
            ),
        ]
    )
    return context


@pytest.fixture
def contextualizer():
    model = AsyncMock()
    model.ainvoke.return_value = AIMessage(
        content="Parental leave entitlements for fathers in Germany"
    )
    return QueryContextualizer(model=model)


@pytest.fixture
def search_service():
    service = AsyncMock()
    service.do_hybrid_search.return_value = []
    return service


@pytest.mark.asyncio
async def test_search_uses_contextualized_query(
        user_id,
        conversation_context,
        contextualizer,
        search_service,
):
    """Retrieval should use the rewritten query, not the raw follow-up."""

    search_service.do_hybrid_search.return_value = [
        type(
            "SearchResult",
            (),
            {
                "chunk_id": uuid4(),
                "document_id": uuid4(),
                "content": "Eligible employees may apply for parental leave.",
                "file_name": "employee-handbook.pdf",
                "page_number": 12,
            },
        )()
    ]


    tool = create_search_documents_tool(
        search_service=search_service,
        user_id=user_id,
        query_contextualizer=contextualizer,
        conversation_context=conversation_context,
    )

    await tool.ainvoke({"query": "What about fathers in Germany?"})

    search_service.do_hybrid_search.assert_awaited_once()

    kwargs = search_service.do_hybrid_search.call_args.kwargs

    assert kwargs["query"] == (
        "Parental leave entitlements for fathers in Germany"
    )
    assert kwargs["user_id"] == user_id


@pytest.mark.asyncio
async def test_returns_empty_list_when_no_documents_found(
        user_id,
        conversation_context,
        contextualizer,
        search_service,
):
    """No results should return an empty list."""

    search_service.do_hybrid_search.return_value = []

    tool = create_search_documents_tool(
        search_service=search_service,
        user_id=user_id,
        query_contextualizer=contextualizer,
        conversation_context=conversation_context,
    )

    result = await tool.ainvoke({"query": "What about fathers in Germany?"})

    assert result == []


@pytest.mark.asyncio
async def test_returns_retrieved_documents(
        user_id,
        conversation_context,
        contextualizer,
        search_service,
):
    """Retrieved search results should be converted to tool output."""

    chunk_id = uuid4()
    document_id = uuid4()

    result = type(
        "SearchResult",
        (),
        {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "content": "The parental leave application process.",
            "file_name": "employee-handbook.pdf",
            "page_number": 12,
        },
    )()

    search_service.do_hybrid_search.return_value = [result]

    tool = create_search_documents_tool(
        search_service=search_service,
        user_id=user_id,
        query_contextualizer=contextualizer,
        conversation_context=conversation_context,
    )

    documents = await tool.ainvoke(
        {"query": "What about fathers in Germany?"}
    )

    assert len(documents) == 1
    assert documents[0].chunk_id == str(chunk_id)
    assert documents[0].document_id == str(document_id)
    assert documents[0].content == (
        "The parental leave application process."
    )
    assert documents[0].filename == "employee-handbook.pdf"
    assert documents[0].page_number == 12


@pytest.mark.asyncio
async def test_contextualizer_receives_current_history(
        user_id,
        conversation_context,
        contextualizer,
        search_service,
):
    """The tool should pass the current conversation history to the rewriter."""

    tool = create_search_documents_tool(
        search_service=search_service,
        user_id=user_id,
        query_contextualizer=contextualizer,
        conversation_context=conversation_context,
    )

    await tool.ainvoke({"query": "What about fathers in Germany?"})

    contextualizer.model.ainvoke.assert_awaited_once()

    messages = contextualizer.model.ainvoke.call_args.args[0]

    assert "employee handbook" in messages[1].content.lower()
    assert "What about fathers in Germany?" in messages[1].content


@pytest.mark.asyncio
async def test_context_isolated_between_conversations(
        user_id,
        contextualizer,
        search_service,
):
    """Different contexts must provide their own histories."""

    first_context = ConversationContext()
    first_context.set_history(
        history=[HumanMessage(content="Tell me about parental leave.")]
    )

    second_context = ConversationContext()
    second_context.set_history(
        history=[HumanMessage(content="Tell me about expense reimbursement.")]
    )

    first_tool = create_search_documents_tool(
        search_service=search_service,
        user_id=user_id,
        query_contextualizer=contextualizer,
        conversation_context=first_context,
    )

    second_tool = create_search_documents_tool(
        search_service=search_service,
        user_id=user_id,
        query_contextualizer=contextualizer,
        conversation_context=second_context,
    )

    await first_tool.ainvoke({"query": "What are the rules?"})
    first_messages = contextualizer.model.ainvoke.call_args.args[0]

    await second_tool.ainvoke({"query": "What are the rules?"})
    second_messages = contextualizer.model.ainvoke.call_args.args[0]

    assert "parental leave" in first_messages[1].content.lower()
    assert "expense reimbursement" in second_messages[1].content.lower()
