class EmbeddingError(Exception):
    """Base exception for embedding errors."""


class TransientEmbeddingError(EmbeddingError):
    """Embedding failed temporarily and can be retried."""


class PermanentEmbeddingError(EmbeddingError):
    """Embedding failed permanently and should not be retried."""
