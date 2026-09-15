from langchain_community.document_loaders import Docx2txtLoader

from ingestion.document_type import DocumentType
from ingestion.loaded_document import LoadedDocument


class WordLoader:

    def load(self, file_path: str) -> list[LoadedDocument]:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()

        return [
            LoadedDocument(
                content=document.page_content,
                source=file_path,
                metadata={
                    **document.metadata,
                    "file_type": DocumentType.DOCX,
                },
            )
            for document in documents
        ]
