# Claude Code task — Stop the OOM crash-loop: fail-on-recovery + split the worker

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. Two code changes (commit
separately), plus Railway config notes. Do not touch the calc engines, extraction
logic, routers, or frontend.

## Background (confirmed from Railway logs)

A document job stuck in `processing` after a redeploy was re-queued on every boot by
`recover_stuck_jobs` (`reset_processing_jobs_to_pending`), re-ran OCR, and was killed
by the container OOM-killer before the worker's `try/except` could mark it failed —
crash loop. (It logged `job_recovered` every boot but never `job_failed`/`job_completed`;
a separate job failed cleanly, proving normal exceptions are already handled.) The
worker runs **in the same process as the web server**, so the OOM took the API down too.

## Change 1 — Recovery marks stuck jobs FAILED, not pending (commit 1)

A job found in `processing` at startup almost certainly crashed the worker. Re-queuing
it re-runs the same crash. Instead, fail it once and let a human retry via the existing
retry endpoint after the memory issue is addressed.

- In `app/repositories/job_repo.py`, replace `reset_processing_jobs_to_pending` with a
  function that selects `status == processing` jobs and sets each to
  `status = failed`, `error = "auto-failed on startup: was processing during a restart; retry manually"`,
  and `completed_at = now(utc)`. Return the affected jobs. (Rename to e.g.
  `fail_stuck_processing_jobs`; update the one caller.)
- In `app/services/job_service.py`, `recover_stuck_jobs` calls the new repo function and
  logs each (`job_failed_on_startup` with job_id + reason). Keep the manual `retry_job`
  path (`reset_job_to_pending`) unchanged — that's how a user re-runs a failed job.
- Update the mirrored tests (search for `reset_processing_jobs_to_pending` /
  `recover_stuck_jobs` in `tests/`): assert a `processing` job becomes `failed` with an
  error set, and that `pending`/`complete` jobs are untouched.

Trade-off to note in the commit: a job interrupted by a *normal* redeploy is also
failed (not resumed). That's intentional and safe — the user retries it from the UI.

## Change 2 — Run the worker as its own process (commit 2)

So an OOM kills only the worker, not the web API.

- `app/main.py` lifespan: keep `init_db()` and `seed_manager(...)`; **remove** the
  background-worker executor (`run_worker` / `stop_event` / `run_in_executor`) and the
  `recover_stuck_jobs` call. The web app no longer runs jobs.
- `app/worker_main.py`: run `init_db()`, then `recover_stuck_jobs(SessionLocal())`
  (the new fail-on-startup behavior), then `run_worker(...)`. The worker service owns
  the job lifecycle end to end.
- `Procfile`: declare both process types:
  ```
  web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  worker: python -m app.worker_main
  ```
- Verify nothing else imports the in-process worker startup; update/keep
  `tests/unit/test_worker_main.py` so it exercises recovery + a single poll.

## Railway config (no code — note in PROGRESS/TODO so it's not forgotten)

- Add a **second Railway service** from the same repo with start command
  `python -m app.worker_main` (Railway doesn't auto-run all Procfile process types —
  the worker needs its own service), sharing the same `DATABASE_URL` and `STORAGE_PATH`.
- Set on the **worker** service: `OMP_THREAD_LIMIT=1` (caps Tesseract's OpenMP threads —
  large memory/CPU reduction) and `MALLOC_ARENA_MAX=2` (tames glibc arena bloat).
- Give the worker service more memory headroom than the web service.

## Optional follow-ups (do NOT do here unless asked) — note as TODO
- Lower OCR DPI 150 → ~110 in `app/parsers/ocr_parser.py`; explicitly free the page
  image per loop (`image.close()`); add an upload size / page-count cap so one huge
  scan can't OOM the worker.
- Harden the `parse_float`-on-empty path (the separate, already-handled
  "could not convert string to float: ''" job failure) to fail with a clearer field-level
  message.

## Definition of done
- `pytest` green (recovery tests updated; worker_main test passes). Commit+push each change.
- Web app starts without running the worker; worker process recovers (fails) stuck jobs
  on boot then polls. A crashed/OOM'd job becomes `failed` once and is never re-queued
  automatically — no crash loop. Add a PROGRESS/TODO line capturing the Railway
  two-service + env-var setup.
