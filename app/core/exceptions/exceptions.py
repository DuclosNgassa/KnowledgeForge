class EmbeddingError(Exception):
    """Base exception for embedding errors."""


class TransientEmbeddingError(EmbeddingError):
    """Embedding failed temporarily and can be retried."""


class PermanentEmbeddingError(EmbeddingError):
    """Embedding failed permanently and should not be retried."""


class TransientSummaryError(Exception):
    """Summarization failed temporarily and can be retried."""

class AppException(Exception):
    """App exception."""
    status_code = 500
    error = "Internal Server Error"

    def __init__(self, message: str = "Internal Server Error"):
        self.message = message
        super().__init__(self.message)


class NotFoundException(AppException):
    status_code = 404
    error = "Not Found"


class BadRequestException(AppException):
    status_code = 400
    error = "Bad Request"


class UnauthorizedException(AppException):
    status_code = 401
    error = "Unauthorized"


class ForbiddenException(AppException):
    status_code = 403
    error = "Forbidden"


class ConflictException(AppException):
    status_code = 409
    error = "Conflict"
