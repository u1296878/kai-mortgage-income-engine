# Task: Case Management

Before doing anything else, read `AGENT.md` in full. Every decision you make must comply with it.
Check `TODO.md` — you are working on Step 3: Case Management.

---

## Context

Document upload is in place. Documents can be uploaded and retrieved.
Documents have a nullable `case_id` and a `PATCH /documents/{id}/case` endpoint to link them to a case.
This task builds the case model and the endpoints that manage cases.

---

## What to build

### `app/models/case.py`
SQLAlchemy model with these fields:
- `id` — UUID, primary key, generated on creation
- `broker_id` — UUID, not nullable. This is the ID of the broker who owns the case. The user model does not exist yet — no FK constraint for now, but the column must exist and must always be set.
- `title` — string, a short human-readable label for the case (e.g. "Johnson Refinance 2024")
- `status` — string, one of: `open`, `in_review`, `complete`. Defaults to `open`.
- `created_at` — datetime, set automatically on creation
- `updated_at` — datetime, updated automatically on every save

### `app/schemas/case.py`
Four Pydantic schemas:
- `CaseCreate` — what comes in to create a case: `title`, `broker_id`
- `CaseUpdate` — what comes in to update a case: `title` and/or `status`, both optional
- `CaseResponse` — what goes back: all fields
- `CaseWithDocuments` — `CaseResponse` plus a `documents` list of `DocumentResponse`

### `app/repositories/case_repo.py`
Five functions, nothing else:
- `create_case(db, case) -> Case`
- `get_case(db, case_id) -> Case` — raises `CaseNotFound` if missing
- `list_cases(db, broker_id=None) -> list[Case]` — returns all cases when `broker_id` is None, filters by broker when provided. This is how manager vs broker access will work once auth is wired in.
- `update_case(db, case_id, updates) -> Case` — raises `CaseNotFound` if missing
- `delete_case(db, case_id) -> None` — raises `CaseNotFound` if missing

### `app/services/case_service.py`
Four functions:
- `create_case(db, title, broker_id) -> Case`
  - Creates and saves the case
  - Calls `log_event("case_created", {"case_id": ..., "broker_id": ..., "title": ...})`
  - Returns the saved case
- `get_case_with_documents(db, case_id, broker_id=None) -> CaseWithDocuments`
  - Fetches the case via repo
  - Fetches documents linked to the case via document repo, passing `broker_id` through
  - Returns combined result
- `update_case(db, case_id, updates) -> Case`
  - Updates and saves the case
  - Calls `log_event("case_updated", {"case_id": ..., "updates": ...})`
  - Returns the updated case
- `list_cases(db, broker_id=None) -> list[Case]`
  - Passes `broker_id` through to repo
  - Returns list of cases

### `app/routers/cases.py`
Five endpoints:
- `POST /cases` — creates a case, returns `CaseResponse`
- `GET /cases` — lists cases, returns `list[CaseResponse]`
- `GET /cases/{case_id}` — returns `CaseResponse`, 404 if not found
- `GET /cases/{case_id}/documents` — returns `CaseWithDocuments`, 404 if not found
- `PATCH /cases/{case_id}` — updates title or status, returns `CaseResponse`
- `DELETE /cases/{case_id}` — deletes case, returns 204

Register this router in `app/main.py`.

---

## Exceptions

Add `CaseNotFound` to `app/exceptions.py`.

---

## Data model note

`broker_id` on the case is a plain UUID column for now with no FK constraint — the user/auth model does not exist yet. When auth is added, `broker_id` will be populated from the JWT token automatically. For now it comes in on `CaseCreate` directly. This is a known temporary state, not a mistake.

---

## Tests

### `tests/unit/test_case_service.py`
- `test_create_case_saves_record` — valid creation, confirm returned case has correct fields
- `test_create_case_sets_status_to_open` — status defaults to open without being specified
- `test_get_case_with_documents_returns_linked_documents` — case with linked documents returns them
- `test_get_case_with_documents_returns_empty_list_when_no_documents` — case with no documents returns empty list
- `test_list_cases_returns_all_when_no_broker_id` — no filter returns all cases
- `test_list_cases_filters_by_broker_id` — broker_id filter returns only that broker's cases
- `test_update_case_changes_title` — title update persists
- `test_update_case_changes_status` — status update persists
- `test_get_missing_case_raises` — missing case_id raises `CaseNotFound`
- `test_delete_missing_case_raises` — missing case_id raises `CaseNotFound`

### `tests/unit/test_cases_router.py`
Use FastAPI `TestClient`. Mock the service layer.
- `test_create_case_returns_case_response` — valid creation returns 200 with correct shape
- `test_list_cases_returns_list` — returns a list
- `test_get_case_returns_case` — valid ID returns case
- `test_get_missing_case_returns_404` — missing ID returns 404
- `test_get_case_with_documents_returns_documents` — returns case and documents
- `test_patch_case_returns_updated_case` — update returns updated case
- `test_delete_case_returns_204` — delete returns 204

---

## Tracking

When this task is complete:
- Move Step 3 from `TODO.md` to `DONE.md`
- Update `PROGRESS.md` with today's date and current status
- `DONE.md` entry: `Step 3: Case management — model, repo, service, router, tests. Cases are broker-scoped via broker_id. List endpoint accepts optional broker_id filter ready for auth.`

---

## Definition of done

- [ ] `POST /cases` creates a case and returns it
- [ ] `GET /cases` returns all cases, accepts optional `broker_id` query param
- [ ] `GET /cases/{id}` returns case, 404 if not found
- [ ] `GET /cases/{id}/documents` returns case with its linked documents
- [ ] `PATCH /cases/{id}` updates title or status
- [ ] `DELETE /cases/{id}` deletes case, returns 204
- [ ] `broker_id` is on the case model and always set on creation
- [ ] `list_cases` and `list_documents_by_case` both accept optional `broker_id` filter
- [ ] `CaseNotFound` added to `exceptions.py`
- [ ] All 17 tests pass
- [ ] No file exceeds 150 lines
- [ ] No dead code, no unused imports
- [ ] `TODO.md`, `DONE.md`, `PROGRESS.md` all updated