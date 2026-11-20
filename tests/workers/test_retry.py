import openai
import pytest

from app.core.exceptions.exceptions import (
    TransientEmbeddingError,
    TransientSummaryError,
    TransientExtractionError,
)
from app.workers.retry import (
    TRANSIENT_API_EXCEPTIONS,
    RETRYABLE_EXCEPTIONS,
)


@pytest.mark.parametrize(
    "exception",
    [
        openai.RateLimitError,
        openai.InternalServerError,
        openai.APIConnectionError,
        openai.ConflictError,
    ],
)
def test_transient_api_exceptions_are_retryable(exception):
    assert exception in TRANSIENT_API_EXCEPTIONS
    assert exception in RETRYABLE_EXCEPTIONS


@pytest.mark.parametrize(
    "exception",
    [
        TransientEmbeddingError,
        TransientSummaryError,
        TransientExtractionError,
    ],
)
def test_application_transient_exceptions_are_retryable(exception):
    assert exception in RETRYABLE_EXCEPTIONS


def test_retryable_exceptions_include_all_transient_exceptions():
    assert set(TRANSIENT_API_EXCEPTIONS).issubset(
        set(RETRYABLE_EXCEPTIONS)
    )


def test_permanent_openai_exceptions_are_not_retryable():
    assert openai.BadRequestError not in RETRYABLE_EXCEPTIONS
    assert openai.AuthenticationError not in RETRYABLE_EXCEPTIONS
