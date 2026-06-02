import asyncio
from contextlib import asynccontextmanager, suppress
from threading import Event

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
from app.routers.income_stream_matching import router as income_stream_matching_router
from app.routers.income_streams import router as income_streams_router
from app.routers.jobs import router as jobs_router
from app.routers.results import router as results_router
from app.seed import seed_manager
from app.workers.job_worker import run_worker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_db = SessionLocal()
    try:
        seed_manager(seed_db)
    finally:
        seed_db.close()
    stop_event = Event()
    loop = asyncio.get_running_loop()
    worker = loop.run_in_executor(
        None,
        run_worker,
        SessionLocal,
        settings.worker_poll_interval,
        stop_event,
    )
    try:
        yield
    finally:
        stop_event.set()
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(worker, timeout=settings.worker_poll_interval + 2)


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
app.include_router(income_streams_router)
app.include_router(income_stream_matching_router)
app.include_router(jobs_router)
app.include_router(results_router)
