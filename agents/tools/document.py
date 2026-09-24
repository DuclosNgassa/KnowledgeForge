from uuid import UUID

from langchain_core.tools import tool

from services.document_service import DocumentService


def create_get_document_metadata_tool(
        user_id: UUID,
        document_service: DocumentService,
):
    @tool
    async def get_document_metadata(document_id: UUID) -> str:
        """Get detailed information about a specific user document.

        Use this tool after search_documents when you need additional
        information about a particular document.

        The document_id must be obtained from a search_documents result.

        Do not invent document IDs.
        """
        document = await document_service.find_document_by_id(
            document_id=document_id,
            user_id=user_id
        )

        if not document:
            return "Document not found"

        return (
            f"ID: {document.id}\n"
            f"Filename: {document.file_name}\n"
            f"Type: {document.document_type}\n"
            f"Source: {document.source}\n"
            f"Status: {document.status}\n"
        )

    return get_document_metadata
