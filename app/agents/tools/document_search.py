from uuid import UUID

from langchain_core.tools import tool

from app.schemas.retrieved_document import RetrievedDocument
from app.services.search_service import SearchService
from app.services.retrieval_collector import RetrievalCollector
from app.services.conversation_context import ConversationContext
from app.services.query_contextualizer import QueryContextualizer


def create_search_documents_tool(
        search_service: SearchService,
        user_id: UUID,
        query_contextualizer: QueryContextualizer,
        conversation_context: ConversationContext,
        request_id: str | None = None,
        collector: RetrievalCollector | None = None,
):
    @tool
    async def search_documents(query: str) -> list[RetrievedDocument]:
        """Search the user´s stored documents for information relevant
         to query.

         Use this tool whenever information from user´s uploaded
         documents is needed
         """

        search_query = await query_contextualizer.contextualize(
            question=query,
            history=conversation_context.history,
        )

        results = await search_service.do_hybrid_search(
            query=search_query,
            user_id=user_id,
            limit=5,
            request_id=request_id,
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

        if collector is not None:
            collector.add(retrieved_documents)

        return retrieved_documents

    return search_documents
