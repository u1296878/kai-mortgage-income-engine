from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.borrowers import router as borrowers_router
from app.routers.cases import router as cases_router
from app.routers.documents import router as documents_router
from app.routers.employment_calculations import router as employment_calculations_router
from app.routers.income import router as income_router
from app.routers.income_stream_matching import router as income_stream_matching_router
from app.routers.income_streams import router as income_streams_router
from app.routers.jobs import router as jobs_router
from app.routers.nontaxable_calculations import router as nontaxable_calculations_router
from app.routers.rental_calculations import router as rental_calculations_router
from app.routers.results import router as results_router
from app.routers.self_employment_calculations import (
    router as self_employment_calculations_router,
)
from app.seed import seed_manager
from app.runtime.worker_runtime import start_worker, stop_worker
from app.services.job_service import recover_stuck_jobs


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    init_db()
    seed_db = SessionLocal()
    try:
        seed_manager(seed_db)
        recover_stuck_jobs(seed_db)
    finally:
        seed_db.close()
    start_worker(SessionLocal, settings.worker_poll_interval)
    try:
        yield
    finally:
        stop_worker(settings.worker_poll_interval + 2)


app = FastAPI(title="Kai Mortgage Income Engine", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(borrowers_router)
app.include_router(cases_router)
app.include_router(documents_router)
app.include_router(employment_calculations_router)
app.include_router(income_router)
app.include_router(income_streams_router)
app.include_router(income_stream_matching_router)
app.include_router(jobs_router)
app.include_router(nontaxable_calculations_router)
app.include_router(rental_calculations_router)
app.include_router(results_router)
app.include_router(self_employment_calculations_router)
