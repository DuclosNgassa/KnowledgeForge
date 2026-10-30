from uuid import UUID

from langchain_core.tools import tool

from app.schemas.retrieved_document import RetrievedDocument
from app.services.query_expander import QueryExpander
from app.services.search_service import SearchService
from app.services.retrieval_collector import RetrievalCollector
from app.services.conversation_context import ConversationContext
from app.services.query_contextualizer import QueryContextualizer


def create_search_documents_tool(
        search_service: SearchService,
        user_id: UUID,
        query_contextualizer: QueryContextualizer,
        conversation_context: ConversationContext,
        query_expander: QueryExpander,
        request_id: str | None = None,
        collector: RetrievalCollector | None = None,
        knowledge_base_ids: list[UUID] | None = None,
):
    @tool
    async def search_documents(query: str) -> list[RetrievedDocument]:
        """Search the user´s stored documents for information relevant
         to query.

         Use this tool whenever information from user´s uploaded
         documents is needed
         """

        # 1. Resolve conversational references.
        search_query = await query_contextualizer.contextualize(
            question=query,
            history=conversation_context.history,
        )

        # 2. Generate alternative search queries.
        queries = await query_expander.expand(search_query)

        # 3. Retrieve and fuse the results.
        results = await search_service.do_multi_query_hybrid_search(
            queries=queries,
            user_id=user_id,
            limit=5,
            request_id=request_id,
            knowledge_base_ids=knowledge_base_ids,
        )

        # results = await search_service.do_hybrid_search(
        #     query=search_query,
        #     user_id=user_id,
        #     limit=5,
        #     request_id=request_id,
        #     knowledge_base_ids=knowledge_base_ids,
        # )

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
