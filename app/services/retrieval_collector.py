from dataclasses import dataclass, field

from app.schemas.retrieved_document import RetrievedDocument


@dataclass
class RetrievalCollector:
    documents: dict[str, RetrievedDocument] = field(default_factory=dict)

    def add(self, documents: list[RetrievedDocument]) -> None:
        for document in documents:
            self.documents[document.chunk_id] = document

    def get_documents(self) -> list[RetrievedDocument]:
        return list(self.documents.values())
