from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.db.database import close_database
from app.observability.logging import setup_logging
from app.observability.middleware import observability_middleware
from app.api.routes import users, embedding, knowledge_bases, document, chat, auth


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

# routing
app.include_router(auth.router)

app.include_router(knowledge_bases.router)

app.include_router(document.router)

app.include_router(embedding.router)

app.include_router(users.router)

app.include_router(chat.router)

# middleware
app.middleware("http")(observability_middleware)
