from app.agents.document_summarization_agent import (
    DocumentSummarizationAgent,
)
from app.core.settings import settings
from langchain.chat_models import init_chat_model
from app.agents.document_extraction_agent import DocumentExtractionAgent


def create_document_extraction_agent() -> DocumentExtractionAgent:
    model = init_chat_model(
        settings.openai_chat_model,
        temperature=0,
        max_retries=5,
    )

    return DocumentExtractionAgent(
        model=model,
        max_concurrent_requests=1,
    )


def create_document_summarization_agent() -> DocumentSummarizationAgent:
    model = init_chat_model(
        settings.openai_chat_model,
        temperature=0,
        max_retries=5,
    )

    return DocumentSummarizationAgent(model=model)
