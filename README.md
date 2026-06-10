# Kai Mortgage Income Engine

Kai Mortgage Income Engine is a local desktop-style app for mortgage income document review. One mortgage professional runs it on their own computer, opens the browser at `localhost`, uploads financial documents, and reviews extracted income results with source references.

There is no login, no cloud storage, and no multi-user role model on this branch. The local server stores data in SQLite and keeps uploaded files on the same machine.

## Requirements

- Python 3.11+
- pip
- Node.js 20+ for the React frontend

For PDF OCR:

```bash
# macOS: brew install tesseract
# Ubuntu: apt-get install tesseract-ocr
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

## Installation

```bash
git clone https://github.com/u1296878/kai-mortgage-income-engine.git
cd kai-mortgage-income-engine
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

For local development and tests:

```bash
pip install -r requirements-dev.txt
```

## Pull And Run

The backend starts with no required environment variables:

```bash
python -m app
```

This creates the local SQLite database and storage directory on first run, starts the in-process background worker, binds the server to `http://127.0.0.1:8000`, and opens the default browser.

For a headless run:

```bash
python -m app --no-browser
```

Ollama setup for fully local extraction is coming in a later conversion step.

## Frontend

The React frontend lives in `frontend/` and covers the local case workflow:

- `/cases` for case listing and creation
- `/cases/:caseId` for upload, job status, extracted fields, source review, and case summary
- `/income/*` worksheet tools for employment, rental, non-taxable, and self-employment income

Run the UI locally:

```bash
cd frontend
npm install
npm run dev
```

By default the Vite dev server proxies `/api/*` to `http://127.0.0.1:8000`.

Frontend tests/build:

```bash
cd frontend
npm run test -- --run
npm run build
```

## Environment Variables

All variables are optional for local boot.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | OS app-data SQLite file | SQLAlchemy database URL used by the app. |
| `STORAGE_PATH` | OS app-data `storage/` folder | Local folder where uploaded documents are stored. |
| `WORKER_POLL_INTERVAL` | `5` | Seconds between background worker job polls. |
| `APP_PORT` | `8000` | Localhost port used by `python -m app`. |
| `NO_BROWSER` | `false` | Set true to prevent `python -m app` from opening a browser. |
| `OCR_DPI` | `150` | DPI used when rasterizing PDF pages for OCR. |
| `OCR_MAX_WORKERS` | `4` | Maximum process-pool workers for multi-page OCR. |
| `OCR_PAGE_TIMEOUT_SECONDS` | `60` | Per-page OCR timeout before the job fails with a page-specific error. |
| `OCR_THREAD_LIMIT` | `1` | Tesseract/OpenMP thread limit set inside OCR workers. |

## Running Tests

```bash
pytest
```

The current backend suite has 449 tests. The current frontend suite has 25 tests.

## Local Access Model

The app has one local identity for legacy `broker_id` columns while the schema is being simplified. API endpoints are open on localhost and do not require `Authorization` headers. The frontend opens directly into the case workflow.

## Income Streams

Results can be grouped into case-level income streams such as employment, rental, or bank-statement income. When a case has income streams, case summary totals use stream annual incomes instead of blindly summing every result. This avoids double-counting when multiple documents support the same income source.

Income stream matching endpoints provide deterministic suggestion previews and high-confidence auto-apply. Manual assignments are preserved by default, and same-case validation prevents cross-case linking.

Cases can include borrowers (`primary` and `co_borrower`), and income streams can be tied to specific borrowers.

## Exercising The Pipeline Manually

These examples assume the API is running at `http://127.0.0.1:8000`. `jq` is optional but makes response handling easier.

```bash
CASE_ID=$(curl -s -X POST http://127.0.0.1:8000/cases \
  -H "Content-Type: application/json" \
  -d '{"title":"Johnson Refinance 2024"}' \
  | jq -r '.id')

DOCUMENT_ID=$(curl -s -X POST http://127.0.0.1:8000/documents/upload \
  -F "doc_type=w2" \
  -F "case_id=$CASE_ID" \
  -F "file=@./sample.pdf;type=application/pdf" \
  | jq -r '.id')

JOB_ID=$(curl -s "http://127.0.0.1:8000/documents/$DOCUMENT_ID/job" | jq -r '.id')

curl -s "http://127.0.0.1:8000/jobs/$JOB_ID" | jq

# Wait a few seconds for the in-process worker to process the pending job.
sleep 6

curl -s "http://127.0.0.1:8000/jobs/$JOB_ID/result" | jq

curl -s "http://127.0.0.1:8000/cases/$CASE_ID/summary" | jq
```

## Pipeline Overview

```text
upload -> store locally -> job created -> worker picks up -> extraction -> result saved -> review
```

## Current Limitations

- W-2, pay stub, tax return, bank statement, and rental-style `other` documents use real PDF parsing.
- `other` currently represents rental-income documents until a dedicated rental document type is introduced.
- Local Ollama extraction wiring is still in progress.
- Matching is rules-based and intentionally conservative; advanced borrower-level and underwriting logic is still future work.
- Legacy `broker_id` columns remain temporarily and are populated with the fixed local identity.
