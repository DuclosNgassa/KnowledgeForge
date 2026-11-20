import openai
from taskiq import Context

from app.core.exceptions.exceptions import TransientEmbeddingError, TransientSummaryError, TransientExtractionError

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
    TransientExtractionError,
)


def is_final_retry(context: Context) -> bool:
    labels = context.message.labels

    retries = int(labels.get("_retries", 0))
    max_retries = int(labels.get("max_retries", 3))

    return retries >= max_retries - 1


def should_fail_prerequisite(
        exception: Exception,
        context: Context,
) -> bool:
    if not isinstance(exception, RETRYABLE_EXCEPTIONS):
        return True

    return is_final_retry(context)
