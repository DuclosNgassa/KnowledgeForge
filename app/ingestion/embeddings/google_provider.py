from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.exceptions.exceptions import TransientEmbeddingError, PermanentEmbeddingError
from app.core.settings import settings
from app.ingestion.embeddings.embedding_provider import EmbeddingProvider
from app.observability.logging import logger


class GoogleEmbeddingProvider(EmbeddingProvider):

    def __init__(self,
                 model: str = settings.google_embedding_model,
                 ):
        self.embeddings = GoogleGenerativeAIEmbeddings(model=model)

    async def embed_documents(self,
                              texts: list[str],
                              ) -> list[list[float]]:

        try:
            return await self.embeddings.aembed_documents(
                texts=texts,
                output_dimensionality=1536,
            )
        except Exception as exc:
            logger.exception(
                "Gemini embedding exception: type=%s, message=%s",
                type(exc).__name__,
                str(exc),
            )

            if self._is_transient_error(exc):
                raise TransientEmbeddingError(
                    "Temporary embedding provider failure"
                ) from exc

            raise PermanentEmbeddingError(
                f"Gemini Embedding failed return {exc}"
            ) from exc

    async def embed_query(
            self,
            text: str,
    ) -> list[float]:
        return await self.embeddings.aembed_query(
            text,
            output_dimensionality=1536,
        )

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        message = str(exc).lower()

        transient_markers = (
            "429",
            "rate limit",
            "resource exhausted",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
            "internal server error",
            "timeout",
            "timed out",
            "connection",
        )

        return any(marker in message for marker in transient_markers)
