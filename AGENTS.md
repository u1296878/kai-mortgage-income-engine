# AGENT.md

Rules for every agent and developer working on this codebase.
Read this before touching anything. These rules do not bend.

> **Direction change (current target): single-user local desktop app.**
> This project is being converted from a hosted multi-user web service into a
> **local application that one mortgage professional runs on their own computer.**
> It starts a local server and opens in the browser, and **all data stays on the
> machine.** The hosted/multi-user version is preserved on the `archive/hosted-multiuser`
> branch — do not build new multi-tenant features on the local branch. When this file
> and older code disagree, **this file wins**; the older hosted assumptions (Postgres,
> Railway, JWT auth, broker/manager roles) are being removed, not maintained.

---

## What This System Is

A local app for one person to process their own mortgage income documents. The user
runs it on their computer, it opens in a browser tab pointed at `localhost`, they upload
financial documents, and the system extracts income fields, organizes them by case, and
returns a reviewable verification result. **No login, no cloud, no other users.** The
borrower's tax data never leaves the machine.

Core pipeline (unchanged in shape):
```
upload → store locally → create job → extract fields → save result → review
```

---

## Deployment / Distribution

- **Runs on:** the user's own computer (Windows/Mac/Linux).
- **Distribution:** the user clones or `git pull`s the repo and runs a single start
  command. No installer build required for now — "pull and run."
- **Database:** **SQLite**, a single local file. No Postgres, no DB server.
- **File storage:** local `storage/` folder. No S3/R2/cloud.
- **Background work:** an **in-process background thread** started by the app — not a
  separate worker process or service. The app starts everything it needs.
- **Extraction model:** a **local Ollama instance** on the same machine (uses the
  user's own CPU/GPU). The app talks to it over `http://localhost:11434`. No hosted AI
  API; document data never leaves the machine.
- **Startup:** one command (e.g. `python -m app` or a `run` script) starts the local
  server and opens the browser. Document this in the README so "the guy can pull and run."

---

## Stack Decisions

These are decided. Do not revisit them without a good reason.

| Concern | Decision | Notes |
|---|---|---|
| Backend | FastAPI + Uvicorn | bound to localhost |
| Database | SQLite | single local file; no server |
| ORM | SQLAlchemy | |
| Validation | Pydantic v2 | |
| File storage | Local `storage/` folder | |
| Background jobs | In-process background thread | no separate worker process |
| Auth | **None** | single local user; no JWT, no roles |
| Extraction | **Local Ollama (LLM) + arithmetic validation** | see Extraction Architecture |
| Income math | Pure deterministic Python (unchanged) | ties out to the worksheets to the cent |
| Distribution | git clone / pull + run command | |

---

## Code Rules

### No dead code
Remove it. Do not comment it out. Unused imports, variables, functions — delete them.
As multi-user/cloud code is removed, delete it outright rather than guarding it behind
flags.

### One responsibility per file
If you need the word "and" to describe what a file does, split it.

### No business logic in route handlers
Route handlers do two things: validate input, call a service. That is all.

### No database access outside the repository layer
Nothing outside `repositories/` queries the database. No exceptions.

### No silent errors
`except: pass` is forbidden. Every error is re-raised, logged, or returned as a
structured response.

### No magic
If something non-obvious is happening, add a one-line comment explaining *why*.

### Keep files small
Aim under 150 lines; 175 is the hard cap. Approaching it means splitting the file.

### Stubs must be honest
Not-yet-implemented work raises `NotImplementedError` with a clear message, or returns
mock data clearly labeled `# STUB` with a `# TODO`. Keep stubs minimal.

### Configuration is never hardcoded
Environment-specific values (paths, the Ollama URL, the model name) come from config.
For a local app, config defaults should "just work" out of the box with zero setup.

### Explicit over implicit
Pass dependencies in. Do not import them inside functions. No global mutable state.

### File paths always use pathlib.Path
Never build paths with string concatenation. This keeps the app working on Windows,
Mac, and Linux — which matters now that it runs on the user's own machine.

---

## Architecture Rules

### Layer order
```
Router → Service → Repository → DB
              ↘ Storage (files)
              ↘ Extraction (parser → Ollama → validation)
```
Nothing skips a layer.

### No frontend-to-database access
All data access goes through the API. The browser talks to the local server only.

### Document storage paths come from internal IDs only
Never derive a file storage path from user input. Use internal IDs.

### Single user — no authorization layer
There is one user and one data scope. Do not add per-user filtering, roles, login, or
tokens. If a genuine multi-user need returns later, it goes on a separate branch, not
into this one.

---

## Domain Rules

### Document types are an enum, not free strings
Valid types: `pay_stub`, `w2`, `tax_return`, `bank_statement`, `other`.
They drive extraction logic and must be consistent everywhere.

### Extraction results always reference their source document
Every extracted field carries the document ID it came from, plus page and (for PDFs)
bounding box. A field value without a source location is incomplete and must not be
saved. This powers click-to-source review in the UI.

### Income logic is isolated and deterministic
Income calculations, totals, and consistency checks live in `app/income/` only. Nothing
else does income math. **This engine stays pure rules-based Python** — it already ties
out to the production worksheets to the cent and must not be replaced by an LLM. The LLM
is for *reading documents*, never for *computing income*.

---

## Extraction Architecture

Document processing is two separate concerns. Keep them separate.

### Parsers — getting content out of the file
`app/parsers/`: take a file and return text and/or page images plus coordinates. They
know nothing about mortgage documents or income fields.
```
pdf_parser.py     — text + coordinates for digital PDFs
ocr_parser.py     — OCR for scanned PDFs/images (text the model can read)
```

### Extractors — turning content into structured fields (LLM-based)
`app/extractors/`: send the parsed content to the **local Ollama model** with a fixed
output schema and get back structured fields (the same `ExtractedField` shape used
today), each with a value, a source reference, and a confidence.

- Tax returns and other financial forms vary too much across tax-software vendors and
  scans for positional/regex rules to be reliable. The LLM reads the labeled lines.
- **Determinism comes from validation, not from the model.** Run the model at
  temperature 0 **and** validate every result arithmetically (below).
- Prefer **OCR-to-text then a text model** over a vision model — it is far lighter on
  local hardware. Use a vision model only if text+OCR proves insufficient.
- Keep the extractor behind the existing
  `extraction_service.extract_fields(document_id, file_path, doc_type) -> list[ExtractedField]`
  interface so the model/host can be swapped without touching callers.

### Validation / reconciliation — the safety net
After extraction, check the numbers against the form's own arithmetic before trusting
them (e.g. Schedule C: line 31 = line 29 − line 30; 1040: total income = sum of parts;
AGI = total income − adjustments). A field that fails its check is **flagged for human
review**, never silently used. This is what makes LLM extraction safe without a large
labeled dataset: the document validates itself.

### Rules
- Parsers never know the document type.
- Extractors never read files directly — they take parsed content.
- Every extracted field includes page number and bounding box (see Source References).
- Nothing downstream consumes an unvalidated, low-confidence field without a review flag.

---

## Source References

Every extracted field must store exactly where it came from, so the user can click any
income figure and jump to the spot in the source PDF (rendered with PDF.js, highlighted
at the bounding box). Required shape per field:
```json
{ "field": "schedule_c_net_profit", "value": 94380, "document_id": "abc123",
  "page": 8, "bounding_box": { "x1": 240, "y1": 380, "x2": 410, "y2": 400 },
  "confidence": 0.98 }
```
- `document_id` and `page` always required. `bounding_box` required for PDF fields.
- For scanned docs, coordinates come from the OCR step. Same structure, same rules.

---

## Exception Rules

Use named domain exceptions in `app/exceptions.py` (e.g. `DocumentNotFound`,
`UnsupportedDocumentType`, `ExtractionFailed`, `ExtractionLowConfidence`). Do not throw
raw `ValueError`/`Exception` for domain errors. Add a named exception whenever a new
meaningful failure mode appears.

---

## Testing Rules

### Every module has tests
No module ships without a test file.

### Test behavior, not implementation
Tests call the public interface and assert on outcomes, not private internals.

### Unit tests are fast and isolated
No database, filesystem, or network in unit tests. Mock only what you don't own —
**including the Ollama call.** Do not hit a real model in unit tests; use a recorded/
fake response. Income-math tests stay pure and deterministic.

### Integration test covers the full pipeline
At least one test walks upload → job → extraction (with a stubbed model) → validation →
result saved → result retrieved, against a temp SQLite DB.

### Validation is tested explicitly
Every reconciliation rule has a test for the passing case and at least one failing case
that proves the field gets flagged for review.

### Tie-out tests stay
The worksheet tie-out tests (`tests/tieout/`, the Excel oracle) are the income engine's
regression net. Keep them green. The income math must not drift.

### Readable, independent, AAA
Descriptive names, Arrange/Act/Assert with blank-line separation, no test depends on
another, cover the unhappy paths.

---

## What Good Looks Like

- A new reader understands any file in under two minutes.
- The app starts with one command and opens in the browser with zero cloud setup.
- Document data never leaves the machine.
- Every extracted number is either validated against the form's arithmetic or flagged
  for review — never silently wrong.
- The income math ties out to the worksheets to the cent, and the tie-out tests prove it.
- Every failure mode has a name and a test.
