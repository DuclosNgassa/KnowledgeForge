# from openai import OpenAI
#
# from app.core.settings import settings
#
# client = OpenAI(api_key=settings.openai_api_key)
#
# response = client.responses.create(
#     model="gpt-4o-mini",
#     input="Write a one-sentence bedtime story about a unicorn.",
# )
#
# print(response.output_text)


# import asyncio
#
# from openai import AsyncOpenAI
#
# async def main():
#     async with AsyncOpenAI() as client:
#         response = await client.embeddings.create(
#             model="text-embedding-3-small",
#             input=["KnowledgeForge async embedding test"],
#         )
#         print("Embedding dimensions:", len(response.data[0].embedding))
#
# if __name__ == "__main__":
#     asyncio.run(main())


# import asyncio
#
# from app.dependencies import get_openai_embedding_provider
#
#
# async def main():
#     provider = get_openai_embedding_provider()
#     embedding = await provider.embed_query(
#         "KnowledgeForge async embedding test"
#     )
#     print("Embedding dimensions:", len(embedding))
#
#
# if __name__ == "__main__":
#     asyncio.run(main())


import asyncio
import traceback

import nest_asyncio

original_apply = nest_asyncio.apply


def traced_apply(*args, **kwargs):
    print("\n=== nest_asyncio.apply() called ===")
    traceback.print_stack()
    return original_apply(*args, **kwargs)


nest_asyncio.apply = traced_apply

print("Before RAGAS:", asyncio.run.__module__)

from ragas import SingleTurnSample

print("After RAGAS:", asyncio.run.__module__)
