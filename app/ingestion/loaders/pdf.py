from langchain_community.document_loaders import PyPDFLoader

from app.ingestion.models.document_type import DocumentType
from app.ingestion.models.loaded_document import LoadedDocument
from pypdf import PdfReader


class PdfLoader:
    def load(self, file_path: str) -> list[LoadedDocument]:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        reader = PdfReader(file_path)
        page_labels = reader.page_labels
        # print("Document in PDF Loader", documents)
        result = []

        for document in documents:
            page_index = document.metadata.get("page")

            printed_label = None
            if (
                    isinstance(page_index, int)
                    and 0 <= page_index < len(page_labels)
            ):
                printed_label = page_labels[page_index]

            result.append(
                LoadedDocument(
                    content=document.page_content,
                    source=file_path,
                    metadata={
                        **document.metadata,
                        "file_type": DocumentType.PDF,
                        "pdf_page_number": (
                            page_index + 1
                            if isinstance(page_index, int)
                            else None
                        ),
                        "printed_page_label": printed_label,
                    },
                )
            )

        return result
