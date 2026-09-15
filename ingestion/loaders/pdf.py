from langchain_community.document_loaders import PyPDFLoader

from ingestion.document_type import DocumentType
from ingestion.loaded_document import LoadedDocument


class PdfLoader:
    def load(self, file_path: str) -> list[LoadedDocument]:
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        return [
            LoadedDocument(
                content=document.page_content,
                source=file_path,
                metadata={
                    **document.metadata,
                    "file_type": DocumentType.PDF,
                },
            )
            for document in documents
        ]
