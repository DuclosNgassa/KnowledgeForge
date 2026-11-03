from langchain.chat_models import init_chat_model

from app.agents.document_summarization_agent import (
    DocumentSummarizationAgent,
)
from app.core.settings import settings


def create_document_summarization_agent() -> DocumentSummarizationAgent:
    model = init_chat_model(
        settings.openai_chat_model,
        temperature=0,
    )

    document_summarization_agent = DocumentSummarizationAgent(model=model)

    return document_summarization_agent
