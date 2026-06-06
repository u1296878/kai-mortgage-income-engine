# Claude Code task — Wire + persist the rental engine (preview, save, summary)

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule (layering, no DB outside `repositories/`, no
   business logic in routers, named exceptions, files < ~175 lines, one
   responsibility per file, every module tested, don't mock what you own, commit/push
   per validated set, keep `PROMPT.md` out of commits).
2. `docs/income-engine-spec.md` section 4 (rental) — the calc authority.
3. The rental engine you are wiring: `app/income/rental.py`,
   `app/schemas/rental_inputs.py`.
4. **The employment slices are your file-for-file template — mirror them.** Build the
   rental equivalent of each:
   - stateless: `app/routers/income.py` (the `/income/employment/calculate` route),
     `app/services/employment_income_service.py`, `app/schemas/income_results.py`
   - persistence: `app/models/employment_calculation.py`,
     `app/repositories/employment_calculation_repo.py`,
     `app/services/employment_calculation_service.py`,
     `app/routers/employment_calculations.py`,
     `app/services/case_summary_builder.py` + `app/services/result_service.py`
     (the summary fold-in), and the tests
     `tests/integration/test_employment_calculations_router.py`,
     `tests/unit/test_employment_calculation_service.py`.

Goal: a broker can preview a rental worksheet, save it to a case, see it listed, and
have its income count in the case summary. Rental is **per-property** (one saved
calculation = one property); a case may have several.

This task touches no extraction, no `Result`/pipeline/worker, no `income_service.py`,
and no self-employment / non-taxable work.

---

## Part A — Backend: stateless preview (commit when green)

Mirror the employment stateless slice:

- `app/schemas/income_results.py` (or a new `rental_results.py` if it keeps files
  small) — Pydantic response models mirroring the engine dataclasses `RentalResult`
  and `RentalYearResult`.
- `app/services/rental_income_service.py` — thin: take a `RentalProperty`, call
  `compute_rental_income`, map the dataclass to the response model, `log_event`.
- `app/routers/income.py` — add `POST /income/rental/calculate` (auth required, body
  `RentalProperty`, returns the rental result). Map `InvalidRentalInput` → 422,
  following the existing exception-mapping style.

Tests: extend `tests/integration/test_income_router.py` — 401 unauthenticated; 200
returning the qualifying figure + per-year breakdown; 422 on a `schedule_e` body with
no years / `investment` with no `monthly_pitia` / `lease` with no `gross_monthly_rent`.

## Part B — Backend: persist + fold into case summary (commit separately)

Mirror the employment persistence slice exactly:

- `app/models/rental_calculation.py` — `RentalCalculation`: `id`, `case_id`
  (not null), `broker_id` (not null, denormalized for scoping), `borrower_id` (nullable),
  `label` (nullable — e.g. property address), `inputs` (JSON `RentalProperty`
  snapshot), `qualifying_monthly` (float), `annual_income` (float =
  `qualifying_monthly * 12` — **may be negative for a rental loss; do not clamp**),
  `breakdown` (JSON), `created_at`. Register in `app/models/__init__.py`
  (table created by `create_all`; no `schema_compat` change for a new table).
- `app/repositories/rental_calculation_repo.py` — `create`, `get`, `list_by_case`,
  `delete` (order `list_by_case` by `created_at, id`, like the employment repo).
- `app/exceptions.py` — add `RentalCalculationNotFound`.
- `app/services/rental_calculation_service.py` — `create_calculation`,
  `list_calculations_by_case`, `get_calculation`, `delete_calculation`, using the
  same `_get_accessible_case` broker/manager scoping; run the engine, persist, and
  `log_event` on create/delete.
- Schemas — `RentalCalculationCreate` (`RentalProperty` + optional `borrower_id`,
  `label`) and `RentalCalculationResponse` (with `breakdown`).
- `app/routers/rental_calculations.py` — case-scoped `POST/GET/GET-by-id/DELETE`
  under `/cases/{case_id}/rental-calculations`; map `CaseNotFound` /
  `RentalCalculationNotFound` → 404, `InvalidRentalInput` → 422. Register in `main.py`.
- Case summary: extend `case_summary_builder.build_case_summary` with a
  `rental_calculations` parameter and add their `annual_income` to the total
  **additively, alongside the employment-calculation total**:

  ```
  total = (stream_total if income_streams else result_total)
          + employment_calc_total
          + rental_calc_total
  ```

  A rental loss (negative `annual_income`) therefore reduces the total — correct.
  Keep the existing documented double-count caveat. Add `rental_calculations` to
  `CaseSummaryResponse`. Fetch them (scoped) in `result_service.get_case_summary`.

Tests (mirror the employment ones):

- `tests/unit/test_rental_calculation_service.py` — create persists & computes the
  right totals; broker scoping (other broker's case → `CaseNotFound`); manager
  access; list/get/delete; missing/cross-case → `RentalCalculationNotFound`.
- Extend the case-summary unit test — saved rental calcs add to the total, and a
  **negative** rental calc reduces it.
- `tests/integration/test_rental_calculations_router.py` — 401; create 200 then it
  appears in `GET /cases/{id}/summary` total; cross-broker 404; scoped list; delete
  204 then gone.

## Part C — Frontend (commit separately)

Mirror the employment UI (`EmploymentIncomePage`, `EmploymentSaveToCase`,
`EmploymentCalculationsPanel`, the API client, types, and their tests):

- `frontend/src/api/income.ts` — add `calculateRentalIncome`,
  `saveRentalCalculation(caseId, payload)`, `listRentalCalculations(caseId)`,
  `deleteRentalCalculation(caseId, id)`; add types to `types/api.ts`.
- A rental worksheet page with conditionally-shown fields: pick `property_class`
  and `method`; for `schedule_e` show up to two year blocks (months + the Schedule E
  line items); for `lease` show `gross_monthly_rent` + vacancy; show `monthly_pitia`
  only for `investment`. Calculate (preview) shows the breakdown; "Save to case"
  persists (with an optional label/address). Keep the standalone preview working.
- On `CaseDetailPage`, add a "Rental income" panel listing saved rental calcs
  (label, monthly, annual) with delete, consistent with the employment panel. The
  case summary total already reflects them via the summary endpoint.
- Keep components small (factor subcomponents). Frontend tests (vitest): preview,
  save, and list/delete on the case page (API mocked).

## Out of scope
- No extraction, no `Result`/pipeline changes, no editing saved calcs yet
  (create + delete only — note edit as future work), no dedupe vs. streams.
- No self-employment or non-taxable work.

## Workflow & definition of done
- Backend: `pytest` fully green. Frontend: `npm run test` + `npm run build` pass.
  Commit+push each part.
- New table via `create_all`; scoping enforced in the service; exceptions mapped;
  rental losses flow through negative into the summary; files within size limits;
  no dead code.
- A broker can compute a rental property (incl. an investment with PITIA and a lease),
  save it to a case, see it listed, watch the summary total move by its annual income
  (including downward for a loss), and delete it.
- Add a line to `PROGRESS.md`/`TODO.md`: rental wired + persisted + in case summary;
  next = the non-taxable engine, then self-employment (Form 1084, needs SAM rows
  113–443 transcribed into spec section 5 first).
