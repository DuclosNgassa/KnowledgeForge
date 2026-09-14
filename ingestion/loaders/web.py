from langchain_community.document_loaders import WebBaseLoader

from ingestion.models import LoadedDocument


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
                    "file_type": "web",
                    "url": url,
                },
            )
            for document in documents
        ]
