from uuid import UUID

from langchain_core.tools import tool

from app.observability.langfuse import langfuse
from app.services.document_service import DocumentService


def create_get_document_metadata_tool(
        user_id: UUID,
        document_service: DocumentService,
        knowledge_base_ids: list[UUID] | None = None,
):
    @tool
    async def get_document_metadata(document_id: UUID) -> str:
        """Get detailed information about a specific user document.

        Use this tool after search_documents when additional document
        information is needed. Only access documents within the current
        session's knowledge-base scope.
        """
        with langfuse.start_as_current_observation(
                as_type="span",
                name="get_document_metadata",
                input={"document_id": str(document_id)},
        ) as observation:
            document = await document_service.find_document_by_id(
                document_id=document_id,
                user_id=user_id,
            )

            if document is None:
                observation.update(output={"found": False})
                return "Document not found"

            # Enforce the session's knowledge-base scope.
            if (
                    knowledge_base_ids is not None
                    and document.knowledge_base_id not in knowledge_base_ids
            ):
                observation.update(output={"found": False})
                return "Document not found"

            observation.update(
                output={
                    "found": True,
                    "filename": document.file_name,
                    "type": document.document_type,
                    "source": document.source,
                    "status": str(document.status),
                }
            )

            return (
                f"ID: {document.id}\n"
                f"Filename: {document.file_name}\n"
                f"Type: {document.document_type}\n"
                f"Source: {document.source}\n"
                f"Status: {document.status}\n"
            )

    return get_document_metadata