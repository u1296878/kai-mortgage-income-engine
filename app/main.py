from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.init_db import init_db
from app.routers.documents import router as documents_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Kai Mortgage Income Engine", lifespan=lifespan)
app.include_router(documents_router)
