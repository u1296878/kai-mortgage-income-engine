# Claude Code task — Wire + persist non-taxable income (preview, save, summary)

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule (layering, no DB outside `repositories/`, no
   business logic in routers, named exceptions, files < ~175 lines, one
   responsibility per file, every module tested, don't mock what you own, commit/push
   per validated set, keep `PROMPT.md` out of commits).
2. `docs/income-engine-spec.md` section 3 — the calc authority.
3. The non-taxable engine you are wiring: `app/income/nontaxable.py`,
   `app/schemas/nontaxable_inputs.py`.
4. **The rental wire+persist slice is your file-for-file template — mirror it.**
   Build the non-taxable equivalent of each:
   - stateless: the `/income/rental/calculate` route in `app/routers/income.py`,
     `app/services/rental_income_service.py`, `app/schemas/rental_results.py`
   - persistence: `app/models/rental_calculation.py`,
     `app/repositories/rental_calculation_repo.py`,
     `app/services/rental_calculation_service.py`,
     `app/routers/rental_calculations.py`, the `case_summary_builder` +
     `result_service` fold-in, and the tests
     `tests/integration/test_rental_calculations_router.py`,
     `tests/unit/test_rental_calculation_service.py`.

Goal: a broker can preview a non-taxable source, save it to a case, see it listed,
and have its income count in the case summary. One saved calculation = one source;
a case may have several.

This task touches no extraction, no `Result`/pipeline/worker, no `income_service.py`,
no rental/employment/self-employment changes.

## Key design difference from rental

This tab has **two source kinds** with different fields: non-taxable income
(`NonTaxableSource`, three methods) and Social Security (`SocialSecuritySource`, two
methods). Use **one** model / endpoint set / panel carrying a `kind` discriminator
(`income` | `social_security`) rather than duplicating everything. The request
carries `kind` plus the matching source fields; the service validates that the
fields for the declared `kind` are present and dispatches to
`compute_nontaxable_income` or `compute_social_security`. `annual_income` is always
`monthly * 12` (non-taxable income is never negative).

---

## Part A — Backend: stateless preview (commit when green)

- `app/schemas/nontaxable_results.py` (small new file) — Pydantic response model
  mirroring the engine dataclass `NonTaxableResult`.
- A request model (in `nontaxable_inputs.py`) — `kind` + optional `income` /
  `social_security` source.
- `app/services/nontaxable_income_service.py` — thin: validate the `kind`/fields,
  dispatch to the right engine function, map to the response model, `log_event`.
- `app/routers/income.py` — add `POST /income/nontaxable/calculate` (auth required).
  Map `InvalidNonTaxableInput` → 422.

Tests: extend `tests/integration/test_income_router.py` — 401; 200 for an income
source and for a Social Security source; 422 when the declared `kind`'s required
fields are missing.

## Part B — Backend: persist + fold into case summary (commit separately)

Mirror the rental persistence slice:

- `app/models/nontaxable_calculation.py` — `NonTaxableCalculation`: `id`, `case_id`
  (not null), `broker_id` (not null), `borrower_id` (nullable), `label` (nullable —
  e.g. "Child support", "SSI"), `kind` (str), `inputs` (JSON source snapshot),
  `monthly` (float), `annual_income` (float = `monthly * 12`), `breakdown` (JSON),
  `created_at`. Register in `app/models/__init__.py` (table via `create_all`).
- `app/repositories/nontaxable_calculation_repo.py` — `create`, `get`,
  `list_by_case`, `delete` (order by `created_at, id`).
- `app/exceptions.py` — add `NonTaxableCalculationNotFound`.
- `app/services/nontaxable_calculation_service.py` — `create/list/get/delete` with
  the `_get_accessible_case` broker/manager scoping; run the engine, persist,
  `log_event` on create/delete.
- Schemas — `NonTaxableCalculationCreate` (the request + optional `borrower_id`,
  `label`) and `NonTaxableCalculationResponse` (with `breakdown`).
- `app/routers/nontaxable_calculations.py` — case-scoped `POST/GET/GET-by-id/DELETE`
  under `/cases/{case_id}/nontaxable-calculations`; map `CaseNotFound` /
  `NonTaxableCalculationNotFound` → 404, `InvalidNonTaxableInput` → 422. Register in
  `main.py`.
- Case summary: add a `nontaxable_calculations` parameter to
  `case_summary_builder.build_case_summary` and add their `annual_income` to the
  total, **alongside the employment- and rental-calculation totals**:

  ```
  total = (stream_total if income_streams else result_total)
          + employment_calc_total + rental_calc_total + nontaxable_calc_total
  ```

  Keep the documented double-count caveat. Add `nontaxable_calculations` to
  `CaseSummaryResponse`; fetch them (scoped) in `result_service.get_case_summary`.

Tests (mirror the rental ones): service (persist/compute both kinds, scoping,
manager access, list/get/delete, missing/cross-case not-found); summary additive
total; integration (401, create then in summary total, cross-broker 404, scoped
list, delete 204).

## Part C — Frontend (commit separately)

Mirror the rental UI (`RentalIncomePage` / save-to-case / case panel / API client /
types / tests):

- `frontend/src/api/income.ts` — add `calculateNontaxableIncome`,
  `saveNontaxableCalculation(caseId, payload)`, `listNontaxableCalculations(caseId)`,
  `deleteNontaxableCalculation(caseId, id)`; add types.
- A non-taxable worksheet page: pick `kind` (income / Social Security), then the
  method, with conditionally-shown fields per method (gross / taxable / current
  monthly; gross-up rate). Preview shows the monthly figure + taxable/eligible split;
  "Save to case" persists with an optional label. Keep the standalone preview working.
- On `CaseDetailPage`, add a "Non-taxable income" panel listing saved sources
  (label, kind, monthly, annual) with delete, consistent with the other panels.
- Keep components small. Frontend tests (vitest): preview (both kinds), save, and
  list/delete on the case page (API mocked).

## Out of scope
- No extraction, no `Result`/pipeline changes, no editing saved calcs (create +
  delete only), no dedupe vs. streams. No self-employment work.

## Workflow & definition of done
- Backend: `pytest` fully green. Frontend: `npm run test` + `npm run build` pass.
  Commit+push each part.
- New table via `create_all`; scoping enforced; exceptions mapped; one model/endpoint
  set handles both kinds; files within size limits; no dead code.
- A broker can compute a non-taxable income source and a Social Security source, save
  them to a case, see them listed, watch the summary total rise, and delete them.
- Add a line to `PROGRESS.md`/`TODO.md`: non-taxable wired + persisted + in case
  summary — Income-Worksheet and Rental-Worksheet now fully covered; next = transcribe
  SAM rows 113–443 into spec section 5, then build the self-employment (Form 1084) engine.
