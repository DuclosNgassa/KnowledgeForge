from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import engine, create_tables
from routers import users, auth, knowledge_bases, document, embedding


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("Database reset successfully.")
    yield
    await engine.dispose()

app = FastAPI(
    title="KnowledgeForge",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)

app.include_router(knowledge_bases.router)

app.include_router(document.router)

app.include_router(embedding.router)

app.include_router(users.router)
