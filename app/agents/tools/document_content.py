from uuid import UUID

from langchain_core.tools import tool

from app.observability.langfuse import langfuse
from app.services.document_service import DocumentService


def create_get_document_content_tool(
        document_service: DocumentService,
        user_id: UUID,
):
    @tool
    async def get_document_content(document_id: str):
        """Read the content of a specific document

        Use this tool when the user ask for information about a specific
        document and the document_id was obtained from search_documents or
        another trusted tool result

        Do not invent document IDs.
        Only documents belonging to the current user can be accessed
        """
        with langfuse.start_as_current_observation(
                as_type="span",
                name="get_document_content",
                input={
                    "document_id": document_id,
                },
        ) as observation:
            try:
                document_id_uuid = UUID(document_id)
            except ValueError:
                observation.update(
                    output={
                        "error": f"Invalid document ID: {document_id}"
                    }
                )
                return "Invalid document ID"

            document = await document_service.get_document_with_chunks(
                document_id=document_id_uuid,
                user_id=user_id,
            )

            if document is None:
                observation.update(
                    output={
                        "found": False,
                    }
                )
                return "Document not found"

            if not document.chunks:
                return "Document has no content"
            chunks = sorted(
                document.chunks,
                key=lambda chunk: chunk.chunk_index
            )

            content = "\n\n".join(
                (
                    f"[Page {chunk.page_number}]"
                    f"\n{chunk.content}"
                )
                for chunk in chunks
            )

            observation.update(
                output={
                    "found": True,
                    "document_id": str(document.id),
                    "file_name": document.file_name,
                }
            )
            return (
                f"Document: {document.file_name}\n"
                f"document ID: {document.id}\n\n"
                f"{content}"
            )

    return get_document_content
