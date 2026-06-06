# PROGRESS

Last updated: 2026-06-04

Current status: Backend extraction, auth, scoping, income-stream modeling, and borrower ownership are complete. React frontend now supports source-click review, case lifecycle management, broker self-registration, document management actions, failed-job retry, and manager broker activation controls.
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

Phase 5, Step 2 is complete:
- Added authenticated `GET /documents/{document_id}/file` endpoint with broker/manager authorization checks
- Added right-side `react-pdf` document viewer drawer in case detail
- Added click-to-highlight source navigation from extracted fields
- Added coordinate transform for PDF bottom-left bounding boxes to top-left viewer overlays
- Added backend endpoint access tests plus frontend viewer smoke test

Phase 5 management UI pass is complete:
- Broker self-registration is available at `/register`; self-registration always creates broker users
- Case list/detail views now support creating cases, advancing status from `open` to `in_review` to `complete`, deleting cases, unlinking documents, deleting documents, and retrying failed jobs
- Manager-only `/admin/brokers` UI and backend endpoints list brokers and deactivate/reactivate accounts
- Inactive broker login is rejected with `Account is deactivated`

## Income engine in progress

Income engine, Step 1 (employment calc core) is complete:
- New isolated `app/income/` package holds all income math, pure and deterministic — no file/DB/network access, inputs injected.
- `dates.months_between` computes fractional months (partial first/last month) and ties out to the spec examples (full year = 12.0, `2026-01-01`→`2026-04-15` = 3.5).
- `pay_frequency` provides the periods/year table plus a rate-of-pay helper (hourly vs periodic).
- `employment.compute_employment_income` implements the months-weighted blend (`Σearnings / Σmonths`, not an average of period monthlies), the base-pay rate-of-pay line, the Annualize/YTD toggle for variable buckets, and the per-bucket + total breakdown.
- Input models live in `app/schemas/income_inputs.py`; the A/Y toggle is modelled as two booleans (`annualize`/`use_ytd`) so the both-set / both-unset validation error (`InvalidEmploymentInput`) is representable per spec 2.3.
- Tie-out, weighted-blend, rate-of-pay, A/Y toggle, and divide-by-zero/missing-input unhappy paths are all covered by tests; full suite green (306 passing).

Income engine, Step 1b (wire employment engine end-to-end, stateless) is complete:
- Backend: `POST /income/employment/calculate` (auth-required) runs the engine and returns the per-bucket breakdown + total monthly. `app/services/employment_income_service.py` is a thin stateless mapper (engine dataclasses → `app/schemas/income_results.py` response models); `InvalidEmploymentInput` maps to HTTP 422. No persistence — the `Result` model is job/document-bound and does not fit a hand-entered worksheet, so persisting + case-summary integration is the next slice.
- Frontend: an authenticated worksheet form (`/income/employment`, linked in the nav) collects base-pay periods + optional rate-of-pay line and the four variable buckets (periods + A/Y toggle), calls the API, and renders each bucket's qualifying figure, per-period monthly + % change, and the total. Components are factored small (period-rows, variable-bucket, base-pay, result-view) with form mapping in `frontend/src/forms/employmentForm.ts`.
- Tests: backend service + integration (401 / 200 breakdown / 422 A/Y / 422 malformed); frontend page test (fills + submits with API mocked, asserts total renders, asserts A/Y payload).

Income engine, Step 1c (persist employment calculations + case-summary integration) is complete:
- Backend: a new case-scoped `EmploymentCalculation` resource (model + repo + service + router) lets a broker save a computed worksheet to a case (`POST/GET/GET/DELETE /cases/{id}/employment-calculations`). The row stores the `inputs` snapshot, `total_monthly`, `annual_income`, and the full `breakdown` (no recompute on display). Scoping uses the `_get_accessible_case` broker/manager pattern; `EmploymentCalculationNotFound` maps to 404, `InvalidEmploymentInput` to 422. The table is created via `create_all` (no schema_compat change). The stateless preview endpoint is unchanged.
- Case summary: saved calculations are folded into `total_annual_income` additively — `(stream_total if streams else result_total) + sum(calc.annual_income)` — and surfaced as `employment_calculations` on `CaseSummaryResponse`. A saved calc and a stream for the same income would double-count; that is accepted, underwriter-controlled behavior for this slice (documented in code + test).
- Frontend: the worksheet, when opened with `?caseId=`, shows a "Save to case" action (optional label) that persists and returns to the case; the case-detail page gains an "Employment Income" panel listing saved calcs (label, monthly, annual) with delete, and the summary total reflects them.
- Tests: backend service (persist/compute, scoping, manager access, list/get/delete, not-found cases), summary additive total, integration (401, create-then-in-summary, 422 A/Y, cross-broker 404, scoped list, delete-then-gone); frontend (save from form, list + delete on the case page).

Income engine, Step 2 (rental calc core) is complete:
- `app/income/rental.py` is a pure engine: one property in (`RentalProperty` in `app/schemas/rental_inputs.py`), one qualifying monthly figure out, plus a reviewable per-year breakdown — mirroring the employment engine's shape.
- Schedule E annual net per year sums the spec 4.1 line items; rental **losses flow through as negative** (not clamped). Primary 2-4 unit averages annual gross (annual-weighted: `(Σannual)/(Σmonths)`); investment subtracts `monthly_pitia` and averages net monthly (months-weighted). The two classes use different averaging — both proven by tests.
- Lease method applies the 0.25 vacancy factor (`gross × 0.75`); investment additionally subtracts PITIA, primary does not. `months_from_fair_rental_days(days)` = `min(days/30, 12)`, defaulting to 12 when missing.
- Divide-by-zero (zero months) is guarded to 0 (Excel IFERROR); `InvalidRentalInput` covers missing year / gross rent / investment PITIA. Tie-out, both averaging modes, the vacancy factor, loss pass-through, and unhappy paths are all tested; full suite green (344 passing).

Income engine, Step 2b (wire + persist rental) is complete — mirrors the employment slices:
- Stateless preview: `POST /income/rental/calculate` (auth-required) runs the engine and returns the qualifying figure + per-year breakdown; `rental_income_service` maps engine dataclasses → `app/schemas/rental_results.py`; `InvalidRentalInput` → 422.
- Persistence: a case-scoped `RentalCalculation` resource (model + repo + service + router) lets a broker save a computed property to a case (`POST/GET/GET/DELETE /cases/{id}/rental-calculations`), storing the `inputs` snapshot, `qualifying_monthly`, `annual_income` (not clamped — negative for a loss), and the `breakdown`. Same `_get_accessible_case` broker/manager scoping; `RentalCalculationNotFound` → 404.
- Case summary: rental `annual_income` is folded into the total **alongside** employment, additively; a rental loss reduces the total. Surfaced as `rental_calculations` on `CaseSummaryResponse`.
- Frontend: a rental worksheet (`/income/rental`, linked in nav) with conditional fields — property class / method selects, Schedule-E year blocks, lease (gross rent + vacancy) and investment (PITIA) inputs shown as relevant; Calculate previews, "Save to case" persists; the case-detail page gains a Rental Income panel (list + delete) and the summary total reflects saved rentals.
- Tests: backend (stateless 200/422, service persist/compute incl. negative loss + scoping + list/get/delete, summary adds + negative reduces, integration), frontend (preview, lease payload, save, list + delete on the case page).

Income engine, Step 3 (non-taxable + Social Security calc core) is complete:
- `app/income/nontaxable.py` is a pure engine: one source in (`NonTaxableSource` / `SocialSecuritySource` in `app/schemas/nontaxable_inputs.py`), one qualifying monthly figure out, plus a small taxable/eligible breakdown where the method splits the amount — mirroring the rental engine's shape.
- Three non-taxable methods (spec 3): `gross_100` (`gross/12`), `total_adjusted` (taxable not grossed up + non-taxable slice grossed up 25%, each term rounded then summed), `current_monthly` (the return's taxable ratio applied to the current monthly amount, then the eligible slice grossed up). Two Social Security methods: `gross_100` and `adjusted` (`(gross + gross*0.15*0.25)/12`). Gross-up rate is a parameter defaulting to 0.25 (spec 1.3).
- Divide-by-zero on the taxable ratio (zero gross) is guarded to 0 (Excel IFERROR); `InvalidNonTaxableInput` covers any method missing its required fields. All three non-taxable methods, both SS methods, a custom gross-up rate, the zero-gross guard, and the missing-field unhappy paths are tested; full suite green (377 passing).

Income engine, Step 3b (wire + persist non-taxable) is complete:
- Backend: `POST /income/nontaxable/calculate` previews non-taxable income and Social Security sources, and `/cases/{id}/nontaxable-calculations` supports case-scoped save/list/get/delete with broker/manager scoping.
- Case summary: saved non-taxable annual income is folded in alongside employment and rental calculations, using the same additive saved-worksheet caveat.
- Frontend: `/income/nontaxable` supports income vs Social Security methods, previews monthly income, saves to a case, and case detail lists/deletes saved sources.
- Income-Worksheet and Rental-Worksheet coverage is now complete; next is transcribing SAM rows 113-443 into spec section 5, then building the self-employment Form 1084 engine.

Remaining for the income engine: transcribe SAM rows 113-443, build self-employment (Form 1084), edit saved calcs (+ optional dedupe vs streams), wire extractors to populate the input models, and finally retire `app/services/income_service.py` in favor of `app/income/`.
