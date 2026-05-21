# DONE

- Step 1: Project scaffold - directory structure, config, exceptions, db session, audit stub, server starts cleanly.
- Step 2: Document upload and storage - model, repo, service, router, tests. Documents upload without a case ID. Case linking via PATCH endpoint.
- Step 3: Case management - model, repo, service, router, tests. Cases are broker-scoped via broker_id. List endpoint accepts optional broker_id filter ready for auth.
- Step 4: Job queue - model, repo, service, router, tests. Jobs created automatically on document upload. Claim mechanism is atomic with SELECT FOR UPDATE SKIP LOCKED.
- Step 5: Extraction stub and results - extraction service stub, result model, income service, result service, router, tests. Full pipeline shape exists. Extraction returns hardcoded fields in correct shape with source references.
- Step 6: Background worker - polling worker runs inside FastAPI lifespan, picks up pending jobs, runs extraction, saves results, marks jobs complete or failed. Full pipeline operational with stub data.
- Step 7: Smoke test and README - full broker workflow tested end to end, dependency override leak fixed, README documents installation, running, and manual curl walkthrough.
