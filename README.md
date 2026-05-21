# Kai Mortgage Income Engine

Kai Mortgage Income Engine is a local-first FastAPI backend for internal mortgage document processing. Brokers upload financial documents, the system stores them by case, creates processing jobs, extracts income fields, and returns reviewable income verification results with source references.

## Requirements

- Python 3.11+
- pip

## Installation

```bash
git clone https://github.com/u1296878/kai-mortgage-income-engine.git
cd kai-mortgage-income-engine
pip install -r requirements.txt
```

## Running locally

```bash
uvicorn app.main:app --reload
```

The background worker starts automatically with the app and polls for pending jobs.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./local.db` | SQLAlchemy database URL used by the app. |
| `STORAGE_PATH` | `./storage` | Local folder where uploaded documents are stored. |
| `WORKER_POLL_INTERVAL` | `5` | Seconds between background worker job polls. |

## Running tests

```bash
pytest
```

Expected test count after this step: 71.

## Exercising the pipeline manually

These examples assume the API is running at `http://127.0.0.1:8000`. `jq` is optional but makes response handling easier.

```bash
BROKER_ID="11111111-1111-1111-1111-111111111111"

CASE_ID=$(curl -s -X POST http://127.0.0.1:8000/cases \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Johnson Refinance 2024\",\"broker_id\":\"$BROKER_ID\"}" \
  | jq -r '.id')

DOCUMENT_ID=$(curl -s -X POST http://127.0.0.1:8000/documents/upload \
  -F "doc_type=w2" \
  -F "file=@./sample.pdf;type=application/pdf" \
  | jq -r '.id')

curl -s -X PATCH "http://127.0.0.1:8000/documents/$DOCUMENT_ID/case" \
  -H "Content-Type: application/json" \
  -d "{\"case_id\":\"$CASE_ID\"}" | jq

JOB_ID=$(curl -s "http://127.0.0.1:8000/documents/$DOCUMENT_ID/job" | jq -r '.id')

curl -s "http://127.0.0.1:8000/jobs/$JOB_ID" | jq

# Wait a few seconds for the worker to process the pending job.
sleep 6

curl -s "http://127.0.0.1:8000/jobs/$JOB_ID/result" | jq

curl -s "http://127.0.0.1:8000/cases/$CASE_ID/summary" | jq
```

## Pipeline overview

```text
upload -> store -> job created -> worker picks up -> extraction -> result saved -> broker retrieves
```

## Current limitations

- Extraction returns hardcoded mock data; real PDF parsing is not yet implemented.
- Auth is not implemented; all endpoints are open.
- File storage is local and must be swapped to S3 or Cloudflare R2 before production use.
