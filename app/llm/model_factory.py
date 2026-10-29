from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI

from app.core.settings import settings


def create_chat_model(*, streaming: bool = False):
    provider = settings.chat_model_provider.lower()

    if provider == "google_genai":
        return init_chat_model(
            model=settings.google_chat_model,
            model_provider=provider,
            streaming=streaming
        )

    if provider == "huggingface":
        if not settings.huggingface_api_key:
            raise ValueError("HUGGINGFACE_API_KEY must be configured "
                             "when chat_model_provider='huggingface'.")

        return ChatOpenAI(
            model=settings.huggingface_chat_model,
            base_url=settings.huggingface_base_url,
            api_key=settings.huggingface_api_key,
            streaming=streaming
        )

    raise ValueError(f"Unsupported chat model provider: {provider}")
