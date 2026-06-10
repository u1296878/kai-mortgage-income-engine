# Claude Code task — Revert the worker to in-process (keep recovery/highlight/OCR fixes)

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. One focused change. **Do NOT
touch** the recovery fix (`fail_stuck_processing_jobs` in `job_repo.py` /
`recover_stuck_jobs` in `job_service.py`), the PDF highlight fix (`DocumentViewer.tsx`),
the OCR point-scaling fix (`ocr_parser.py`), or any income engine. We are only undoing
the worker-process split (commit `f24dc1c`).

## Why

Splitting the worker into its own Railway service breaks document processing: with
local-disk storage, the web and worker run in separate containers and don't share
files, and Railway volumes attach to only one service. The crash loop is already solved
by the recovery fix (stuck jobs are now marked `failed`, not re-queued), so the worker
can safely run in-process again until storage is moved to S3/R2.

## Change 1 — `app/main.py`: run the worker as a background thread in the lifespan

Restore the pre-split lifespan (this is exactly how it ran before, and it calls the
**new** `recover_stuck_jobs`, which now fails stuck jobs):

```python
import asyncio
from contextlib import asynccontextmanager, suppress
from threading import Event
# ...existing imports...
from app.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.seed import seed_manager
from app.services.job_service import recover_stuck_jobs
from app.workers.job_worker import run_worker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_db = SessionLocal()
    try:
        seed_manager(seed_db)
        recover_stuck_jobs(seed_db)
    finally:
        seed_db.close()
    stop_event = Event()
    loop = asyncio.get_running_loop()
    worker = loop.run_in_executor(
        None, run_worker, SessionLocal, settings.worker_poll_interval, stop_event,
    )
    try:
        yield
    finally:
        stop_event.set()
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(worker, timeout=settings.worker_poll_interval + 2)
```

(Re-add only the imports that were removed in the split — `asyncio`, `suppress`,
`Event`, `recover_stuck_jobs`, `run_worker`. Leave the router includes and CORS as-is.)

## Change 2 — `Procfile`: one line

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Remove the `worker:` line.

## Keep `app/worker_main.py` as-is

Leave it in place (and its test). It's still a valid standalone runner
(`python -m app.worker_main`, documented in the README) and will be the entry point
when the worker is split for real after the S3/R2 storage swap. Do not delete it.

## Railway config (no code)
Single service again. Set `OMP_THREAD_LIMIT=1` and `MALLOC_ARENA_MAX=2`, and give it
more memory headroom. With the recovery fix in place, an OOM now causes a single
restart (the stuck job is marked failed on the next boot) instead of a crash loop.

## Definition of done
- `pytest` green; `npm run build` still fine (no frontend change here). The web app
  starts, recovers (fails) any stuck job, and runs the worker thread; uploaded
  documents process again in the same container.
- Commit+push. Note in PROGRESS/TODO: worker is in-process again for local storage;
  re-split the worker only after moving storage to S3/R2 (then re-add the `worker:`
  process and a second Railway service).
