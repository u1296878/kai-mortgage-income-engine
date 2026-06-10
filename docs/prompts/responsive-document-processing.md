# Task: make document processing responsive (no freezing on large/scanned PDFs)

Read `AGENTS.md` first and follow every rule in it (layer order, no business logic in
routers, DB only in repositories, named exceptions, files under ~175 lines, tests for
every module, commit + push after each green change set).

## The problem

Processing a scanned multi-page tax return is slow and the UI appears to freeze.
Root causes, all in the worker path — investigate and confirm before changing anything:

- `app/services/job_processing_service.py` processes an **entire document in one
  blocking call** (`extraction_service.extract_fields`). For a scanned PDF this OCRs
  every page sequentially.
- `app/workers/job_worker.py` is a single-threaded poll loop that handles **one job at
  a time**, so one large OCR job starves every other job in the queue.
- `app/parsers/ocr_parser.py` OCRs pages **sequentially** and lets Tesseract
  oversubscribe CPU threads.
- The extraction hot path (`app/extractors/tax_return_locator.py` and the per-line
  anchor/`nearest_money_value` lookups) is roughly **O(n²)** over OCR blocks — the main
  latency cost on scanned docs (~14k blocks → tens of seconds).
- `app/models/job.py` has `status` but **no progress fields**, so the frontend has no
  way to show movement and looks frozen.
- A crash or timeout mid-document **loses all work** — there is no checkpointing.

## Goal / acceptance criteria

1. Uploading a document still returns immediately with a job id (keep this; verify it).
2. A large scanned document no longer blocks other jobs from progressing.
3. The frontend can show real progress (e.g. "page 7 of 30", a percentage) that updates
   while the job runs, so nothing looks frozen.
4. Per-page work is **idempotent and resumable**: if the worker restarts, processing
   continues from the last completed page instead of starting over.
5. The extractor's per-document time on a ~30-page scanned return drops substantially
   (target: well under 10s for the field-finding step, separate from OCR), via indexing
   rather than algorithmic guesswork.
6. Every changed/added module has tests. Cover the unhappy paths (timeout on a page,
   worker restart mid-document, a page that yields no blocks).

## Implementation plan (do in this order, commit after each)

### 1. Index the extractor hot path (biggest, lowest-risk win)
In `tax_return_locator.py` and the Schedule C / Schedule E extractors, build a
**per-page index of blocks once** (e.g. `dict[page] -> list[block]`, and within a page
bucket blocks by rounded y-coordinate) and have line-anchor / nearest-value lookups read
from that index instead of scanning the full block list per call. Pure refactor — the
extracted fields must be byte-for-byte identical. Add a test that asserts identical
output on a fixture before/after, plus a timing assertion on a large synthetic block set.

### 2. Parallelize and bound OCR per page
In `ocr_parser.py`, OCR pages with a **process pool** (default workers =
`min(cpu_count(), 4)`), set `OMP_THREAD_LIMIT=1` in each worker to stop Tesseract
oversubscribing, and apply a **per-page timeout** so one bad page can't hang the job
(raise a named exception, e.g. `PageOcrTimeout`, recorded against that page — never
`except: pass`). Keep the existing monkeypatch test hooks working. Page count and DPI
come from config, not hardcoded.

### 3. Add progress to the Job + a status endpoint
- Add `pages_total` and `pages_done` (and optionally `current_stage`) to
  `app/models/job.py`; update the repo in `app/repositories/job_repo.py` to write them.
  Provide a backward-compatible default/migration (see `app/db/schema_compat.py`).
- Expose progress on the existing job status route (`app/routers/jobs.py`) via the
  service layer — a `percent` derived field is fine. Router stays thin (validate + call
  service), per AGENTS.md.

### 4. Make the document job resumable per page
Refactor `job_processing_service.py` so a document job processes **one page (or a small
batch) per worker iteration**, persists the partial blocks/fields and increments
`pages_done`, and re-claims the same job until all pages are done — then runs the
field-assembly + draft-creation step once. On restart it resumes from `pages_done`.
Keep extraction logic in the extractors; the service only orchestrates. Persist partial
blocks somewhere cheap (a `job_pages` table via a new repo, or the storage layer) — do
not hold them only in memory.

### 5. Let the queue make progress under load
Allow the worker to interleave jobs (process a page from job A, then a page from job B)
or run a small pool of workers, so a 30-page document doesn't block a 1-page pay stub.
Claim semantics must stay safe (no two workers grab the same page); keep all DB access
in the repository layer.

### 6. Frontend: show progress instead of a blocking spinner
Wherever the UI waits on a job, poll the status endpoint on an interval (or add SSE) and
render a progress bar from `pages_done/pages_total`. The page must stay interactive while
a job runs — no synchronous blocking call on the document-processing path.

## Constraints / don't

- Don't put extraction or DB logic in routers or in the worker loop body.
- Don't introduce Redis/Celery — AGENTS.md keeps the DB-backed queue for now; this is a
  "swap later" decision, not part of this task.
- Don't change any qualifying-income math or the extracted field shapes (source
  references with page + bounding box are a hard requirement).
- Keep files under the 175-line cap; split where needed.

## Definition of done
All tests green (`pytest`), a scanned multi-page return processes with visible
incrementing progress, other jobs are not starved while it runs, killing and restarting
the worker resumes mid-document, and the extracted fields are unchanged from before the
refactor. Commit and push after each green step.
