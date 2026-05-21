from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.init_db import init_db
from app.routers.cases import router as cases_router
from app.routers.documents import router as documents_router
from app.routers.jobs import router as jobs_router
from app.routers.results import router as results_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Kai Mortgage Income Engine", lifespan=lifespan)
app.include_router(cases_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(results_router)
