from ai.embedding_provider import EmbeddingProvider
from openai import AsyncOpenAI


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(self,
                 api_key: str,
                 model: str = "text-embedding-3-small"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def embed(self,
                    texts: list[str], ) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        return [
            item.embedding
            for item in response.data
        ]
