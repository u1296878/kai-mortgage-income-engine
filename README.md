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

## Local environment setup

Copy the example env file and fill in required values:

    cp .env.example .env

Edit `.env` and set at minimum:

    JWT_SECRET_KEY=any-long-random-string-for-local-dev

To create the first manager account on startup, also set:

    MANAGER_EMAIL=manager@example.com
    MANAGER_PASSWORD=your-chosen-password

The app reads `.env` automatically via pydantic-settings.

## Running locally

```bash
uvicorn app.main:app --reload
```

The background worker starts automatically with the app and polls for pending jobs.

To run the worker as its own process:

```bash
python -m app.worker_main
```

## Frontend (Phase 5 foundation)

A React frontend now lives in `frontend/` and covers:

- `/login` for JWT sign-in
- `/cases` for broker/manager case listing
- `/cases/:caseId` for upload, job status, extracted fields, and case summary review

Run the UI locally:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

By default the Vite dev server proxies `/api/*` to `http://127.0.0.1:8000`.
To point at Railway, set `VITE_API_PROXY_TARGET` to your Railway backend URL in `frontend/.env`.

Frontend tests/build:

```bash
cd frontend
npm run test
npm run build
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./local.db` | SQLAlchemy database URL used by the app. |
| `STORAGE_PATH` | `./storage` | Local folder where uploaded documents are stored. |
| `WORKER_POLL_INTERVAL` | `5` | Seconds between background worker job polls. |
| `JWT_SECRET_KEY` | required | JWT signing secret. Provide a long random value in `.env` or deployment env vars. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Access token lifetime in minutes. |
| `MANAGER_EMAIL` | empty | Optional first-run manager seed email. |
| `MANAGER_PASSWORD` | empty | Optional first-run manager seed password. |

## Running tests

```bash
pytest
```

Expected test count after this step: 248.

## Authentication

Local JWT auth is available. Users register and log in at `/auth/register` and `/auth/login`, then call protected endpoints with `Authorization: Bearer <token>`. `/auth/me` returns the current authenticated user.

Brokers can access only their own cases, documents, jobs, results, and summaries. Managers can access all records.

Production note: manager provisioning is still a hardening item. Before production, manager account creation should move behind an admin-only or deployment-controlled flow.

## Income streams

Results can be grouped into case-level income streams (for example employment, rental, or bank-statement income) through authenticated stream endpoints. When a case has income streams, case summary totals use stream annual incomes instead of blindly summing every result. This avoids double-counting when multiple documents support the same income source.

Income stream matching endpoints now provide deterministic suggestion previews and high-confidence auto-apply. Manual assignments are preserved by default, and same-case validation prevents cross-case linking.

Cases can now include borrowers (`primary` and `co_borrower`), and income streams can be tied to specific borrowers. Borrower and stream assignment routes follow the same broker/manager scope rules and same-case validation used elsewhere in the pipeline.

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
  -F "case_id=$CASE_ID" \
  -F "file=@./sample.pdf;type=application/pdf" \
  | jq -r '.id')

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
- Matching is rules-based and intentionally conservative; advanced borrower-level and underwriting logic is still future work.
- Manager account provisioning is not production-hardened yet.
- Railway deployment setup is not finalized yet; production environment variables and Postgres wiring still need to be applied.
- File storage is local and must be swapped to S3 or Cloudflare R2 before production use.
