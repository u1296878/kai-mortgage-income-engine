# Claude Code task — Persist employment calculations & fold into case summary

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule. Especially: layer order
   (Router → Service → Repository → DB), no DB access outside `repositories/`,
   no business logic in routers, named domain exceptions, files under ~175 lines,
   one responsibility per file, every module has tests, don't mock what you own
   (use a real test DB), commit/push per validated change set, keep `PROMPT.md` out
   of commits.
2. The engine + stateless slice you are building on:
   `app/income/employment.py`, `app/schemas/income_inputs.py`,
   `app/services/employment_income_service.py`, `app/routers/income.py`.
3. **Pattern to imitate exactly — the case-scoped income-stream resource:**
   `app/routers/income_streams.py`, `app/services/income_stream_service.py`
   (note `_get_accessible_case(...)` for broker/manager scoping),
   `app/repositories/income_stream_repo.py`, `app/models/income_stream.py`.
4. `app/services/result_service.py` + `app/services/case_summary_builder.py`
   (how the case summary total is built today) and `app/db/init_db.py` +
   `app/models/__init__.py` (how a model/table gets registered).

## Goal

Let a broker **save** a computed employment worksheet to a case, list/delete saved
calculations, and have their income **count toward the case summary total**. The
existing stateless preview endpoint stays as-is (preview vs. save are distinct).

---

## Part A — Backend (do first; commit when green)

### Data model
Create `app/models/employment_calculation.py` — `EmploymentCalculation`:

- `id` (str uuid, pk), `case_id` (str, not null), `broker_id` (str, not null —
  denormalized for scoping, exactly like `IncomeStream`), `borrower_id`
  (str | None), `label` (str | None — e.g. employer name),
- `inputs` (JSON — the `EmploymentInput` snapshot, so it can be re-displayed/edited
  and audited),
- `total_monthly` (float), `annual_income` (float = `total_monthly * 12`),
- `breakdown` (JSON — the per-bucket `EmploymentResult`, so display needs no recompute),
- `created_at` (tz-aware, like the other models).

Register it: add the import + `__all__` entry in `app/models/__init__.py`.
`init_db`'s `create_all` then creates the table on SQLite and Postgres — a brand-new
table needs **no** `schema_compat` change (that file is only for adding columns to
pre-existing tables).

### Repository
Create `app/repositories/employment_calculation_repo.py`: `create`, `get`,
`list_by_case`, `delete`. DB access lives only here.

### Exceptions
Add `EmploymentCalculationNotFound` to `app/exceptions.py`.

### Service
Create `app/services/employment_calculation_service.py` (keep the stateless
`calculate_*` in `employment_income_service.py` — one responsibility per file):

- `create_calculation(db, case_id, employment_input, borrower_id, label, current_user)`
  — scope the case with the `_get_accessible_case` pattern, run the engine
  (`compute_employment_income`), persist inputs + total_monthly + annual_income +
  breakdown, return the row.
- `list_calculations_by_case(db, case_id, current_user)` — scoped.
- `get_calculation(db, case_id, calc_id, current_user)` — scoped; raise
  `EmploymentCalculationNotFound` if missing or not in this case.
- `delete_calculation(db, case_id, calc_id, current_user)` — scoped.
- Emit `log_event` on create and delete (audit).

### Schemas
Add to the income schema files: `EmploymentCalculationCreate` (an `EmploymentInput`
plus optional `borrower_id`, `label`) and `EmploymentCalculationResponse`
(`id, case_id, borrower_id, label, total_monthly, annual_income, breakdown,
created_at`).

### Router (case-scoped, mirror income_streams)
Add to `app/routers/income.py` (or a small dedicated router, your call — register it
in `main.py` if new):

- `POST   /cases/{case_id}/employment-calculations`  → create
- `GET    /cases/{case_id}/employment-calculations`  → list
- `GET    /cases/{case_id}/employment-calculations/{calc_id}` → get
- `DELETE /cases/{case_id}/employment-calculations/{calc_id}` → 204

Map `CaseNotFound`/`EmploymentCalculationNotFound` → 404,
`InvalidEmploymentInput` → 422, following the existing exception-mapping style.

### Case summary integration
Fold saved employment calculations into the total. In `result_service.get_case_summary`
fetch them (scoped) and pass to `case_summary_builder.build_case_summary`. Define:

```
total = (stream_total if income_streams else result_total)
        + sum(calc.annual_income for calc in employment_calculations)
```

Add `employment_calculations` to `CaseSummaryResponse` so the UI can show them.
**Document this additive behavior** in a code comment and a test: manually-saved
employment income adds on top of document/stream income. (A saved calc and a stream
representing the same income would double-count — that's an accepted, underwriter-
controlled behavior for this slice; note it, don't try to dedupe here.)

### Tests
- `tests/unit/test_employment_calculation_service.py` — create persists & computes
  the right totals; broker scoping (another broker's case → `CaseNotFound`); manager
  access; list/get/delete; delete removes; missing calc → `EmploymentCalculationNotFound`.
- Extend the case-summary unit test — saved calcs add to the total additively.
- `tests/integration/test_employment_calculations_router.py` — 401 unauthenticated;
  create 200 then the calc appears in `GET /cases/{id}/summary` total; cross-broker
  404; list scoped; delete 204 then gone. Reuse existing integration auth fixtures.

---

## Part B — Frontend (after Part A green; commit separately)

- `frontend/src/api/income.ts` — add `saveEmploymentCalculation(caseId, payload)`,
  `listEmploymentCalculations(caseId)`, `deleteEmploymentCalculation(caseId, id)`.
  Add the types to `frontend/src/types/api.ts`.
- Let the existing employment worksheet save into a case: when opened in a case
  context, add a "Save to case" action (optional label field) that calls the persist
  endpoint; keep the standalone preview working unchanged.
- On `CaseDetailPage`, add an "Employment income" panel that lists saved
  calculations (label, monthly, annual) with a delete action, consistent with the
  existing case-detail panels. Ensure the displayed case summary total reflects the
  persisted calcs (it will, via the summary endpoint).
- Keep components small — factor subcomponents rather than growing one file.
- Frontend test (vitest): saving from the form (API mocked) and listing/deleting a
  saved calc on the case page.

## Out of scope
- No changes to the `Result` model, extraction pipeline, worker, or `income_service.py`.
- No auto-extraction. No rental / non-taxable / self-employment.
- No editing of a saved calculation yet (create + delete only); note it as future work.

## Workflow & definition of done
- Backend: `pytest` fully green (new tests pass, nothing existing breaks). Commit+push.
- Frontend: `npm run test` and `npm run build` pass. Commit+push.
- New table created via `create_all`; scoping enforced in the service; domain
  exceptions mapped; files within AGENTS.md size limits; no dead code.
- A broker can compute a worksheet, save it to a case, see it listed, see the case
  summary total rise by its annual income, and delete it.
- Add a line to `PROGRESS.md`/`TODO.md`: employment calcs persisted + in case summary;
  next = rental and non-taxable engines (and later: edit saved calcs, dedupe vs streams).
