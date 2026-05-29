# PROGRESS

Last updated: 2026-05-29

Current status: Phase 3 broker/manager data scoping complete. Phase 2 real PDF extraction is complete, JWT auth foundation is complete, and private mortgage workflow routes now enforce ownership.
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

## Phase 3 complete

The private workflow is protected by JWT auth and service-layer authorization. Brokers are isolated to their own records across cases, documents, jobs, results, and summaries. Managers have full visibility across broker-owned records.

Ready for Phase 4 focus:
- Income stream model for cases with multiple income sources
- Production admin/user provisioning
- Production storage and deployment hardening
- Expanded audit logging
