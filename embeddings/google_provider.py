from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.settings import settings
from embeddings.embedding_provider import EmbeddingProvider


class GoogleEmbeddingProvider(EmbeddingProvider):

    def __init__(self,
                 model: str = settings.google_embedding_model,
                 ):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model,
            output_dimensionality=1536,
        )

    async def embed_documents(self,
                              texts: list[str],
                              ) -> list[list[float]]:
        return await self.embeddings.aembed_documents(
            texts=texts,
        )

    async def embed_query(
            self,
            text: str,
    ) -> list[float]:
        return await self.embeddings.aembed_query(
            text
        )
