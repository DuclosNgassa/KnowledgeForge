import openai

from app.core.exceptions.exceptions import TransientEmbeddingError, TransientSummaryError

TRANSIENT_API_EXCEPTIONS = (
    openai.RateLimitError,
    openai.InternalServerError,
    openai.APIConnectionError,
    openai.ConflictError,
)

RETRYABLE_EXCEPTIONS = (
    *TRANSIENT_API_EXCEPTIONS,
    TransientEmbeddingError,
    TransientSummaryError,
)
