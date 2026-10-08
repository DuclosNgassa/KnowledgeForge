from openai import RateLimitError, APIConnectionError, APITimeoutError, APIStatusError

from app.core.exceptions.exceptions import TransientEmbeddingError, PermanentEmbeddingError
from app.core.settings import settings
from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from langchain_openai import OpenAIEmbeddings


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(self,
                 model: str = settings.openai_embedding_model,
                 ):
        self.embeddings = OpenAIEmbeddings(model=model)

    async def embed_documents(self,
                              texts: list[str],
                              ) -> list[list[float]]:
        try:
            return await self.embeddings.aembed_documents(
                texts=texts,
            )
        except (
                RateLimitError,
                APIConnectionError,
                APITimeoutError,) as exc:
            raise TransientEmbeddingError(
                "Temporary OpenAI embedding failure"
            ) from exc

        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise TransientEmbeddingError(
                    f"OpenAI server error: {exc.status_code}"
                ) from exc

            raise PermanentEmbeddingError(
                f"OpenAI API error: {exc.status_code}"
            ) from exc

    async def embed_query(
            self,
            text: str,
    ) -> list[float]:
        return await self.embeddings.aembed_query(
            text
        )
