# Kai Mortgage Income Engine

Kai Mortgage Income Engine is a local-first FastAPI backend for internal mortgage document processing. Brokers upload financial documents, the system stores them by case, creates processing jobs, extracts income fields, and returns reviewable income verification results with source references.

## Requirements

- Python 3.11+
- pip

For PDF parsing:

```bash
# macOS: brew install tesseract
# Ubuntu: apt-get install tesseract-ocr
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
```

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

To run the worker as its own process:

```bash
python -m app.worker_main
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./local.db` | SQLAlchemy database URL used by the app. |
| `STORAGE_PATH` | `./storage` | Local folder where uploaded documents are stored. |
| `WORKER_POLL_INTERVAL` | `5` | Seconds between background worker job polls. |
| `JWT_SECRET_KEY` | local development secret | JWT signing secret. Set a secure value in production. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime in minutes. |

## Running tests

```bash
pytest
```

Expected test count after this step: 181.

## Authentication

Local JWT auth is available. Users register and log in at `/auth/register` and `/auth/login`, then call protected endpoints with `Authorization: Bearer <token>`. `/auth/me` returns the current authenticated user.

Brokers can access only their own cases, documents, jobs, results, and summaries. Managers can access all records.

## Exercising the pipeline manually

These examples assume the API is running at `http://127.0.0.1:8000`. `jq` is optional but makes response handling easier.

```bash
curl -s -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"broker@example.com","password":"secret-password"}' | jq

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"broker@example.com","password":"secret-password"}' \
  | jq -r '.access_token')

CASE_ID=$(curl -s -X POST http://127.0.0.1:8000/cases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Johnson Refinance 2024"}' \
  | jq -r '.id')

DOCUMENT_ID=$(curl -s -X POST http://127.0.0.1:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "doc_type=w2" \
  -F "file=@./sample.pdf;type=application/pdf" \
  | jq -r '.id')

curl -s -X PATCH "http://127.0.0.1:8000/documents/$DOCUMENT_ID/case" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"case_id\":\"$CASE_ID\"}" | jq

JOB_ID=$(curl -s "http://127.0.0.1:8000/documents/$DOCUMENT_ID/job" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.id')

curl -s "http://127.0.0.1:8000/jobs/$JOB_ID" \
  -H "Authorization: Bearer $TOKEN" | jq

# Wait a few seconds for the worker to process the pending job.
sleep 6

curl -s "http://127.0.0.1:8000/jobs/$JOB_ID/result" \
  -H "Authorization: Bearer $TOKEN" | jq

curl -s "http://127.0.0.1:8000/cases/$CASE_ID/summary" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Pipeline overview

```text
upload -> store -> job created -> worker picks up -> extraction -> result saved -> broker retrieves
```

## Current limitations

- W-2, pay stub, tax return, bank statement, and rental-style `other` documents use real PDF parsing.
- `other` currently represents rental-income documents until a dedicated rental document type is introduced.
- JWT auth and broker/manager resource scoping are implemented.
- File storage is local and must be swapped to S3 or Cloudflare R2 before production use.
