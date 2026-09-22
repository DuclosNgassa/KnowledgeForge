from uuid import UUID

from langchain_core.tools import tool

from services.similarity_search_service import SimilaritySearchService


def create_search_documents_tool(
        search_service: SimilaritySearchService,
        user_id: UUID,
):
    @tool
    async def search_documents(query: str) -> str:
        """Search the user´s stored documents for information relevant
         to query.

         Use this tool whenever information from user´s uploaded
         documents is needed
         """
        results = await search_service.search(
            query=query,
            user_id=user_id,
            limit=5,
        )

        print("Result of search: ", results)
        if not results:
            return f"No relevant information was found for: {query}"

        return "\n\n".join(
            (
                f"SOURCE: {result.source}\n"
                f"PAGE: {result.page_number}\n"
                f"RELEVANCE: {result.score:.3f}\n"
                f"CONTENT: {result.content}\n"
            )
            for result in results
        )

    return search_documents
