from langchain_community.document_loaders import PyPDFLoader

from ingestion.models import LoadedDocument


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
                    "file_type": "pdf",
                },
            )
            for document in documents
        ]
