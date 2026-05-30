# DONE

- Step 1: Project scaffold - directory structure, config, exceptions, db session, audit stub, server starts cleanly.
- Step 2: Document upload and storage - model, repo, service, router, tests. Documents upload without a case ID. Case linking via PATCH endpoint.
- Step 3: Case management - model, repo, service, router, tests. Cases are broker-scoped via broker_id. List endpoint accepts optional broker_id filter ready for auth.
- Step 4: Job queue - model, repo, service, router, tests. Jobs created automatically on document upload. Claim mechanism is atomic with SELECT FOR UPDATE SKIP LOCKED.
- Step 5: Extraction stub and results - extraction service stub, result model, income service, result service, router, tests. Full pipeline shape exists. Extraction returns hardcoded fields in correct shape with source references.
- Step 6: Background worker - polling worker runs inside FastAPI lifespan, picks up pending jobs, runs extraction, saves results, marks jobs complete or failed. Full pipeline operational with stub data.
- Step 7: Smoke test and README - full broker workflow tested end to end, dependency override leak fixed, README documents installation, running, and manual curl walkthrough.
- Phase 2, Step 1: W-2 PDF parsing - pdf_parser, ocr_parser, w2_extractor. Real extraction replaces stub for w2 doc type. Synthetic W-2 variant extracts wages with real coordinates; IRS and ADP public samples were checked but contain no extractable wage values.
- Phase 2, Step 2: Pay stub parsing - paystub_extractor with keyword search strategy, income_service updated with period-based annualization and cross-check logic. Tested against synthetic pay stub.
- Phase 2, Step 3: Tax return parsing - tax_return_extractor with IRS 1040 line-number and label matching, extraction_service updated to route tax_return through real PDF/OCR parsing, synthetic 1040 generator and unit/integration tests added.
- Phase 2, Step 4: Bank statement parsing - bank_statement_extractor with deposit detection, statement date extraction, total deposits, months sampled, and average monthly deposit calculation. extraction_service updated to route bank_statement through real PDF/OCR parsing. Synthetic statement generator and unit/integration tests added.
- Phase 2, Step 5: Rental income parsing - rental_extractor with Schedule E-style gross rents, expenses, net income, tax year, and property address extraction. extraction_service updated to route other through real PDF/OCR parsing. Synthetic rental generator and unit/integration tests added.
- Phase 2 cleanup and hardening - verified all document types route through real extractors, removed stale stub references, confirmed source-reference and unhappy-path test coverage, refreshed docs after completing real PDF extraction.
- Phase 3, Step 1: JWT auth foundation - user model, password hashing, JWT creation/verification, auth service/repository/router, current-user dependency, and auth tests added.
- Phase 3, Step 2: Broker and manager data scoping - protected private routes with JWT auth, enforced broker ownership in services, allowed manager-wide access, and added authorization tests for cases, documents, jobs, results, and summaries.
- Phase 3 cleanup and hardening - refreshed AGENTS/README/progress tracking after auth and scoping completion, verified private route protection, service-layer authorization, broker isolation, manager visibility, and full test coverage before Phase 4.
- Phase 4, Step 1: Income stream model foundation — added income streams, result assignment, stream-based case summary totals, broker/manager scoping, and tests.
- Phase 4, Step 2: Income stream suggestion and matching - added deterministic heuristics for matching results into streams, same-case validation, suggestion explanations, and tests.
