from ai.embedding_provider import EmbeddingProvider
from langchain_openai import OpenAIEmbeddings


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(self,
                 model: str = "text-embedding-3-small"):
        self.embeddings = OpenAIEmbeddings(model=model)

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
