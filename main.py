from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import engine, Base, create_tables
from routers import users, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await engine.dispose()

app = FastAPI(
    title="KnowledgeForge",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(users.router)
app.include_router(auth.router)
