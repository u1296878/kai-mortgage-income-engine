# TODO

- [x] Phase 2, Step 2: Pay stub PDF parsing
- [x] Phase 2, Step 3: Tax return (1040) PDF parsing
- [x] Phase 2, Step 4: Bank statement PDF parsing
- [x] Phase 2, Step 5: Rental income PDF parsing
- [x] Phase 3, Step 1: JWT auth foundation
- [x] Phase 3, Step 2: broker/manager data scoping across cases, documents, jobs, and results
- [x] Phase 3 cleanup: recap auth/scoping status, refresh stale docs, and verify readiness for Phase 4
- [x] Phase 4, Step 1: income stream model foundation with result assignment and stream-based case summaries
- [x] Phase 4, Step 2: automatic income stream suggestion/matching across supporting documents
- [ ] Phase 4, Step 3: borrower/co-borrower modeling for stream ownership and review workflows
- [ ] Phase 4, Step 4: richer matching heuristics (employer normalization, stronger tax-year and period linking, tie-break tuning)
- [ ] Add production-safe admin or manager provisioning so manager access is not self-service
- [ ] Swap local file storage for S3 or Cloudflare R2 before production
- [ ] Add production deployment configuration
- [ ] Expand audit logging beyond local stdout
