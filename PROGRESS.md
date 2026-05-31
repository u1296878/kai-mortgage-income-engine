# PROGRESS

Last updated: 2026-05-31

Current status: Backend extraction, auth, scoping, income-stream modeling, and borrower ownership are complete. React frontend foundation is now complete and supports the broker workflow against the live backend: login, cases, case detail, upload, job status, extracted fields, source references, and case summary review.
No document types currently use the extraction stub.

- [x] Step 1: Project scaffold
- [x] Step 2: Document upload
- [x] Step 3: Case management
- [x] Step 4: Job queue
- [x] Step 5: Extraction stub and results
- [x] Step 6: Background worker
- [x] Step 7: End-to-end smoke test

## Phase 2 complete

The core pipeline is fully operational with real rules-based PDF extraction for every current document type. Every step from document upload to income verification result is implemented, tested, and documented.

Completed extraction coverage:
- W-2 real extraction
- Pay stub real extraction
- Tax return real extraction
- Bank statement real extraction
- Rental income real extraction through `other`

Auth foundation:
- User registration and login
- JWT access tokens
- Current-user identity via `/auth/me`
- Broker and manager roles stored on users

Broker/manager data scoping:
- Brokers can access only their own cases, documents, jobs, results, and summaries
- Managers can access all records
- Broker case creation uses the authenticated user id instead of trusting request-provided broker_id
- Startup manager seed can create exactly one manager account from `MANAGER_EMAIL` and `MANAGER_PASSWORD` when no manager exists

## Phase 3 complete

The private workflow is protected by JWT auth and service-layer authorization. Brokers are isolated to their own records across cases, documents, jobs, results, and summaries. Managers have full visibility across broker-owned records.

Ready for Phase 4 focus:
- Income stream model for cases with multiple income sources
- Production admin/user provisioning
- Production storage and deployment hardening
- Expanded audit logging

## Phase 4 in progress

Phase 4, Step 1 is complete:
- Income stream model, repository, service, schemas, and router added
- Result-to-stream assignment and removal implemented with same-case validation
- Stream annual income recalculates with deterministic confidence ordering: `high > medium > low`, then most recent result
- Case summaries use stream totals when streams exist and fall back to result totals when streams do not

Phase 4, Step 2 is complete:
- Deterministic match suggestions for case results based on stream type and extracted identifiers
- Explainable suggestion reasons and confidence tiers (`high`, `medium`, `low`)
- Preview and apply endpoints for matching
- High-confidence auto-apply with manual assignment preservation by default
- Same-case validation preserved for brokers and managers during matching and assignment

Phase 4, Step 3 is complete:
- Borrower/co-borrower model added with case and broker ownership
- Borrower CRUD and borrower-to-income-stream assignment endpoints added with broker/manager scoping
- Same-case borrower/stream assignment validation added for brokers and managers
- Case summary now includes borrowers while preserving existing stream-total fallback behavior

## Phase 5 in progress

Phase 5, Step 1 is complete:
- React + TypeScript + Vite frontend scaffold added in `frontend/`
- JWT login and `/auth/me` session bootstrap with protected routes
- Case list and case detail workflow wired to backend API
- Upload flow linked to job polling and result refresh
- Extracted field source references and case summary surfaced in UI
- Frontend baseline tests added for login, auth guard, cases page, and case detail rendering
