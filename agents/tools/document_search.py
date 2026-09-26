from uuid import UUID

from langchain_core.tools import tool

from schemas.retrieved_document import RetrievedDocument
from services.search_service import SearchService


def create_search_documents_tool(
        search_service: SearchService,
        user_id: UUID,
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
        )

        if not results:
            return []

        retrieved_documents = [
            RetrievedDocument(
                chunk_id=str(result.chunk_id),
                document_id=str(result.document_id),
                content=result.content,
                filename=result.file_name,
                page_number=result.page_number,
            )
            for result in results
        ]

        print("retrieved_documents: ", retrieved_documents)

        return retrieved_documents

    return search_documents
