from uuid import UUID

from langchain_core.tools import tool

from schemas.retrieved_document import RetrievedDocument
from services.reranker.base import Reranker
from services.search_service import SearchService


def create_search_documents_tool(
        search_service: SearchService,
        reranker: Reranker,
        user_id: UUID,
        request_id: str | None = None,
):
    @tool
    async def search_documents(query: str) -> list[RetrievedDocument]:
        """Search the user´s stored documents for information relevant
         to query.

         Use this tool whenever information from user´s uploaded
         documents is needed
         """
        results = await search_service.do_hybrid_search(
            query=query,
            user_id=user_id,
            limit=5,
            request_id=request_id,
        )

        if not results:
            return []

        # print("Search result before reranking: ", results)

        reranked_results = await reranker.rerank(
            query=query,
            results=results,
            top_k=5,
            request_id=request_id
        )
        #print("Search result after reranking: ", reranked_results)


        retrieved_documents = [
            RetrievedDocument(
                chunk_id=str(result.chunk_id),
                document_id=str(result.document_id),
                content=result.content,
                filename=result.file_name,
                page_number=result.page_number,
            )
            for result in reranked_results
        ]


        return retrieved_documents

    return search_documents
