from pydantic import BaseModel


class RetrievedDocument(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    filename: str
    page_number: int | None
