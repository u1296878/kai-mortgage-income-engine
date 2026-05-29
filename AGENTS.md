# AGENT.md

Rules for every agent and developer working on this codebase.
Read this before touching anything. These rules do not bend.

---

## What This System Is

A web app for internal mortgage document processing. Brokers and managers log in via browser. Brokers upload financial documents. The system extracts income fields, organizes by case, and returns a reviewable verification result. Only employees of the company use this — it is not public-facing.

Core pipeline:
```
upload → store → create job → extract fields → save result → return to broker
```

---

## Deployment Target

- **Hosting:** Railway
- **Database:** Postgres (SQLite is used in tests only)
- **File storage:** Local `storage/` folder for now — will be swapped to S3 or Cloudflare R2 in a future task. The storage module is isolated so this swap touches one file.
- **Background worker:** Railway worker process running alongside the web server

---

## Stack Decisions

These are decided. Do not revisit them without a good reason.

| Concern | Decision | Notes |
|---|---|---|
| Backend | FastAPI + Uvicorn | |
| Database | Postgres | SQLite for tests only |
| ORM | SQLAlchemy | |
| Validation | Pydantic v2 | |
| File storage | Local `storage/` folder | Swap to S3/R2 later |
| Job queue | DB-backed polling worker | Swap to Redis/Celery later |
| Auth | JWT tokens | Not built yet — stub exists |
| Deployment | Railway | |

---

## Code Rules

### No dead code
Remove it. Do not comment it out. Do not leave it "just in case."
Unused imports, unused variables, unused functions — delete them.

### One responsibility per file
If you need the word "and" to describe what a file does, split it.

### No business logic in route handlers
Route handlers do two things: validate input, call a service. That is all.

### No database access outside the repository layer
Nothing outside `repositories/` queries the database. No exceptions.

### No silent errors
`except: pass` is forbidden. Every error is either re-raised, logged, or returned as a structured response.

### No magic
If something non-obvious is happening, add a one-line comment explaining *why*, not *what*.

### Keep files small
Aim to keep files under 150 lines. If a file is cleaner at slightly more than 150 lines, that is acceptable, but 175 lines is the hard cap. If you are approaching 175 lines, the file needs to be split.

### Stubs must be honest
If something is not implemented yet, raise `NotImplementedError` with a clear message, or return mock data clearly labeled with a `# STUB` comment and a `# TODO` describing what replaces it. Do not expand stub complexity. Keep stubs minimal.

### Configuration is never hardcoded
All environment-specific values (paths, URLs, secrets) come from config. No hardcoded strings for anything that could differ between environments.

### Explicit over implicit
Pass dependencies in. Do not import them inside functions. Do not use global mutable state.

### File paths always use pathlib.Path
Never build file paths with string concatenation. Always use `pathlib.Path`.
This ensures the code works on Windows, Mac, and Linux without changes.

---

## Architecture Rules

### Layer order
```
Router → Service → Repository → DB
              ↘ Storage (files)
```
Nothing skips a layer. Routers do not call repositories. Workers follow the same rule.

### No frontend-to-database access
All data access goes through the API. Always.

### Document storage paths come from internal IDs only
Never derive a file storage path from user input. Use internal IDs.

### Security layers are not built yet — do not close the door on them
Auth, permissions, and audit logging will be added as separate layers.
Do not make decisions now that would require unpicking the codebase to add them later.

### Every broker's data is scoped to them
Every case, document, and result belongs to a broker.
When auth is added, all queries for broker-role users will filter by their ID.
Write queries so this filter can be added without restructuring them.

---

## Domain Rules

### Document types are an enum, not free strings
Valid types: `pay_stub`, `w2`, `tax_return`, `bank_statement`, `other`.
These drive extraction logic. They must be consistent everywhere.

### Extraction results always reference their source document
Every extracted field must carry the document ID it came from.
This is a hard requirement for audit and review.

### Income logic is isolated
Income calculations, totals, and consistency checks live in one place only.
Nothing else does income math. 

### Two roles exist: broker and manager
- Brokers see only their own cases, documents, and results.
- Managers see everything.
- Role enforcement is not built yet but the data model must support it from the start.

---

## Exception Rules

Use named domain exceptions. Do not throw raw `ValueError` or `Exception` for domain errors.
Define exceptions in `app/exceptions.py`. Examples of what belongs there:
- `DocumentNotFound`
- `UnsupportedDocumentType`
- `ExtractionFailed`
- `JobAlreadyProcessed`

When you add a new failure mode that has a meaningful name, add it there.

---

## Testing Rules

### Every module has tests
No module ships without a test file. No exceptions.

### Test the behavior, not the implementation
Tests call the public interface and assert on outcomes.
Tests do not reach into private functions or assert on internal state.

### Unit tests are fast and isolated
Unit tests do not touch the database, the filesystem, or the network.
Use dependency injection and mocking to isolate the unit under test.

### Integration tests cover the full pipeline
At least one integration test walks the entire pipeline end to end:
upload → job created → worker processes → result saved → result retrieved.
This test runs against a real test database (SQLite in-memory or temp file).

### Test file structure mirrors source structure
```
app/services/document_service.py  →  tests/unit/test_document_service.py
app/routers/documents.py          →  tests/unit/test_documents_router.py
app/workers/job_worker.py         →  tests/integration/test_job_worker.py
```

### Tests must be readable
A test is documentation. Someone reading a test for the first time should understand
what the system is supposed to do from the test alone. Name tests descriptively:
`test_upload_creates_pending_job`, not `test_upload` or `test_1`.

### Arrange / Act / Assert — always in that order
Every test has three clear sections. No interleaving. Use a blank line to separate them.
```python
def test_upload_creates_pending_job():
    document = make_fake_document(doc_type="w2")

    result = job_service.create_job_for_document(document)

    assert result.status == "pending"
    assert result.document_id == document.id
```

### Cover the unhappy paths
Every service function that can fail must have at least one test for the failure case.
`DocumentNotFound`, bad input, unsupported type — these must be tested explicitly.

### No test depends on another test
Tests are independent. They do not share state. They do not need to run in order.
Use fixtures for setup. Tear down after every test.

### Do not mock what you own
Only mock external dependencies (filesystem, third-party APIs, OCR tools).
Do not mock your own services or repositories in unit tests — use real instances with a test DB.

---

## What Good Looks Like

- A new engineer reads any file and understands it in under two minutes.
- Every module can be replaced without touching anything outside its layer.
- The full pipeline can be exercised with a single HTTP call sequence.
- Every failure mode has a name and a test.
- No test is a mystery. Every test name says exactly what it is checking.


---

## Source References

Every extracted field must store exactly where it came from in the source document.
A field value without a source location is incomplete and must not be saved.

### Required structure for every extracted field
```json
{
  "field": "w2_wages",
  "value": 88000,
  "document_id": "abc123",
  "page": 1,
  "bounding_box": {
    "x1": 240,
    "y1": 380,
    "x2": 410,
    "y2": 400
  }
}
```

### Rules
- `document_id` — always required. Every field traces back to a specific document.
- `page` — always required. 1-indexed.
- `bounding_box` — required for PDF fields. x1/y1 is top-left, x2/y2 is bottom-right, in PDF points.
- For scanned documents, bounding box coordinates come from the OCR engine. Same structure, same rules.
- The stub extractor does not need real coordinates but must return the correct shape with placeholder values so nothing downstream breaks when real coordinates are added.

### Why this exists
The broker must be able to click any income figure in their results and be taken directly to the exact location in the source document where that number was found. This is a core product requirement, not a nice-to-have.

### How the frontend uses it
The frontend renders PDFs using PDF.js. Each source reference becomes a clickable link that opens the document at the specified page and draws a highlight overlay at the bounding box coordinates. The result record must carry enough information for the frontend to do this without any additional lookups.


---

## Parsing and Extraction Architecture

Document processing is split into two distinct concerns. Keep them separate.

### Parsers — getting text out of the file
Parsers live in `app/parsers/`. They take a file and return raw text plus bounding box coordinates. They know nothing about mortgage documents or income fields.

```
app/parsers/
    pdf_parser.py     — pdfplumber for clean digital PDFs
    ocr_parser.py     — Tesseract for scanned PDFs and images
```

A parser returns a list of text blocks, each with page number and bounding box. That is all it does.

### Extractors — finding fields in the text
Extractors live in `app/extractors/`. They take the raw text blocks from a parser and return structured fields with source references. They know the layout of specific document types. They do not touch files.

```
app/extractors/
    w2_extractor.py
    paystub_extractor.py
    tax_return_extractor.py
    bank_statement_extractor.py
    rental_extractor.py
```

Each extractor is independent. Improving one never touches another.

### How they connect
`extraction_service.py` owns the handoff:
1. Determine document type
2. Call the right parser based on whether the PDF has real text or is a scanned image
3. Pass the result to the matching extractor
4. Return structured fields with source references

### Rules
- Parsers never know what document type they are processing
- Extractors never read files directly
- No extractor imports another extractor
- Rules-based extraction first — regex and known field positions per document type. No LLM unless rules fail.
- Every extracted field must include page number and bounding box coordinates (see Source References section)

### Why rules over LLM
W-2s, pay stubs, and 1040s are standardized forms. Field positions are predictable. Rules-based extraction is free, instant, and deterministic. An LLM is only added as a fallback for documents that do not match known patterns. Do not reach for an LLM when a regex will do.
