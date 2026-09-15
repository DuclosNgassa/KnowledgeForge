from langchain_community.document_loaders import WebBaseLoader

from ingestion.document_type import DocumentType
from ingestion.loaded_document import LoadedDocument


class WebLoader:

    def load(self, url: str) -> list[LoadedDocument]:
        loader = WebBaseLoader(url)
        documents = loader.load()

        return [
            LoadedDocument(
                content=document.page_content,
                source=url,
                metadata={
                    **document.metadata,
                    "file_type": DocumentType.WEB,
                    "url": url,
                },
            )
            for document in documents
        ]
