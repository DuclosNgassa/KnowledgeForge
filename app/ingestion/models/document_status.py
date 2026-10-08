from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"  # Use it later when taskiq still fails after max_retries
    READY = "READY"
