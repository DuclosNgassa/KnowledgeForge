from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"  # Use it later when taskiq still fails after max_retries
    READY = "READY"


class EmbeddingStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentType(StrEnum):
    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"
    WEB = "WEB"


class SummaryStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExtractionStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
