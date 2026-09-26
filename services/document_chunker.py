from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingestion.loaded_document import LoadedDocument
from schemas.document_chunk import DocumentChunkData


class DocumentChunkService:

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def chunk(self, documents: list[LoadedDocument]) -> list[DocumentChunkData]:

        result: list[DocumentChunkData] = []
        chunk_index = 0
        for document in documents:
            chunks = self.spliter.split_text(document.content)

            for chunk in chunks:
                result.append(
                    DocumentChunkData(
                        content=chunk,
                        source=document.source,
                        chunk_index=chunk_index,
                        metadata=document.metadata,
                    )
                )

                chunk_index += 1

        return result
