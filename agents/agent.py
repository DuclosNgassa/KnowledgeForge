from uuid import UUID

import langchain_openai
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

from agents.tools.document_search import create_search_documents_tool
from core.settings import Settings, settings


def create_agent(
        search_service,
        user_id
):
    search_documents = create_search_documents_tool(
        search_service,
        user_id
    )

    model = ChatOpenAI(
        model=settings.openai_chat_model
    )

    return create_deep_agent(
        # model=model,
        model="google_genai:" + settings.google_chat_model,
        tools=[search_documents],
        system_prompt="""
        You are the KnowledgeForge research assistant.
        
        Use the search_documents tool whenever the user´s
        question requires information from
        their stored documents
        
        Always give the result in the format:
            chunk_id: UUID
            document_id: UUID
            content: str
            source: str
            page_number: int
            score: float
        
        Do not invent information that is not supported
        by the retrieved documents.
        """,
    )
