from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.exceptions import AppException
from app.observability.logging import logger


def _error_response(
        request: Request,
        status_code: int,
        error: str,
        message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "error": error,
            "message": message,
            "path": request.url.path,
        },
    )


async def app_exception_handler(
        request: Request,
        exc: AppException,
) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=exc.status_code,
        error=exc.error,
        message=exc.message,
    )


async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=exc.status_code,
        error="HTTP Error",
        message=str(exc.detail),
    )


async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
) -> JSONResponse:
    logger.error(
        "Request validation failed | path=%s | errors=%s",
        request.url.path,
        exc.errors(),
        exc_info=exc,
    )

    return _error_response(
        request=request,
        status_code=422,
        error="Validation Error",
        message="Request validation failed",
    )


async def response_validation_exception_handler(
        request: Request,
        exc: ResponseValidationError,
) -> JSONResponse:
    logger.error(
        "Response validation failed | path=%s | errors=%s",
        request.url.path,
        exc.errors(),
        exc_info=exc,
    )

    return _error_response(
        request=request,
        status_code=500,
        error="Internal Server Error",
        message="The server returned an invalid response",
    )


async def value_error_handler(
        request: Request,
        exc: ValueError,
) -> JSONResponse:
    return _error_response(
        request=request,
        status_code=400,
        error="Bad Request",
        message=str(exc),
    )


async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
) -> JSONResponse:
    logger.exception(
        "Unhandled exception | path=%s | method=%s",
        type(exc).__name__,
        request.url.path,
        request.method,
        exc_info=exc,
    )

    return _error_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="Internal Server Error",
        message="An unexpected error occurred",
    )
