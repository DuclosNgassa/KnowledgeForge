from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db.database import close_database
from app.core.exceptions.exceptions import AppException
from app.observability.logging import setup_logging
from app.observability.middleware import observability_middleware
from app.api.routes import users, embedding, knowledge_bases, document, chat, auth
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions.exception_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    unexpected_exception_handler, value_error_handler, response_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError, ResponseValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_database()


setup_logging()
app = FastAPI(
    title="KnowledgeForge",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(
    AppException,
    app_exception_handler
)

app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    ValueError,
    value_error_handler,
)

app.add_exception_handler(
    ResponseValidationError,
    response_validation_exception_handler,
)

app.add_exception_handler(
    Exception,
    unexpected_exception_handler,
)

# routing
app.include_router(auth.router)

app.include_router(knowledge_bases.router)

app.include_router(document.router)

app.include_router(embedding.router)

app.include_router(users.router)

app.include_router(chat.router)

# middleware
app.middleware("http")(observability_middleware)
