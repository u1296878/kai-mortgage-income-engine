# Claude Code task — Wire + persist self-employment (preview, save, summary)

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule (layering, no DB outside `repositories/`, no
   business logic in routers, named exceptions, files < ~175 lines, one
   responsibility per file, every module tested, don't mock what you own, commit/push
   per validated set, keep `PROMPT.md` out of commits).
2. `docs/income-engine-spec.md` section 5 — the calc authority.
3. The engines you are wiring:
   - personal: `app/income/self_employment.py` (`compute_schedule_b/c/d/
     e_royalty/f`), `app/schemas/self_employment_inputs.py`
   - entity: `app/income/self_employment_entity.py` (`compute_partnership/
     s_corporation/corporation`), `app/schemas/self_employment_entity_inputs.py`
4. **The non-taxable wire+persist slice is your closest template** (it also used a
   `kind` discriminator): `app/services/nontaxable_income_service.py`,
   `app/services/nontaxable_calculation_service.py`,
   `app/models/nontaxable_calculation.py`,
   `app/repositories/nontaxable_calculation_repo.py`,
   `app/routers/nontaxable_calculations.py`, and the rental/nontaxable summary
   fold-in + tests. Mirror that structure.

Goal: a broker can preview a self-employment schedule or entity, save it to a case,
see it listed, and have its income count in the case summary. One saved calculation =
one schedule or entity; a case may have several.

This task touches no extraction, no `Result`/pipeline/worker, no `income_service.py`,
no other engines.

## Key design: one discriminated model with registry dispatch

Self-employment has **eight calc kinds**: `schedule_b`, `schedule_c`, `schedule_d`,
`schedule_e_royalty`, `schedule_f` (personal) and `partnership`, `s_corporation`,
`corporation` (entity). Do **not** build eight of everything. Use one model / one
endpoint set / one panel carrying a `kind` discriminator, and a **registry** mapping
each kind to its (input model, compute function):

```
KIND_REGISTRY = {
  "schedule_c": (ScheduleCInput, compute_schedule_c),
  "partnership": (PartnershipInput, compute_partnership),
  ... all eight ...
}
```

A request carries `kind` + a `payload` object. The service looks up the registry,
validates the payload into the right input model, runs the compute function, and
**normalizes** both result shapes (personal `SelfEmploymentResult` and entity
`SelfEmploymentEntityResult`) to a common response: `{kind, qualifying_monthly,
annual_income, breakdown}` where `breakdown` is the full result as JSON and
`annual_income = qualifying_monthly * 12` (**may be negative for a loss; do not
clamp**). Put this dispatch in the service, not the router. An unknown `kind` or an
invalid payload → `InvalidSelfEmploymentInput` (→ 422 at the router).

---

## Part A — Backend: stateless preview (commit when green)

- `app/schemas/self_employment_results.py` — the unified response model above.
- Request model — `kind` + `payload` (object) (+ for Part B, optional `borrower_id`,
  `label`).
- `app/services/self_employment_income_service.py` — the registry + dispatch +
  normalize + `log_event`.
- `app/routers/income.py` — add `POST /income/self-employment/calculate` (auth
  required). Map `InvalidSelfEmploymentInput` → 422.

Tests: extend `tests/integration/test_income_router.py` — 401; 200 for a personal
schedule (e.g. `schedule_c`) and an entity (e.g. `partnership`) returning the
qualifying figure + breakdown; 422 on an unknown `kind` and on a payload missing
required fields.

## Part B — Backend: persist + fold into case summary (commit separately)

Mirror the non-taxable persistence slice:

- `app/models/self_employment_calculation.py` — `SelfEmploymentCalculation`: `id`,
  `case_id` (not null), `broker_id` (not null), `borrower_id` (nullable), `label`
  (nullable — e.g. business name), `kind` (str), `inputs` (JSON payload snapshot),
  `qualifying_monthly` (float), `annual_income` (float = `qualifying_monthly * 12`,
  may be negative), `breakdown` (JSON), `created_at`. Register in
  `app/models/__init__.py` (table via `create_all`).
- `app/repositories/self_employment_calculation_repo.py` — `create`, `get`,
  `list_by_case`, `delete` (order by `created_at, id`).
- `app/exceptions.py` — add `SelfEmploymentCalculationNotFound`.
- `app/services/self_employment_calculation_service.py` — `create/list/get/delete`
  with `_get_accessible_case` broker/manager scoping; reuse the Part A dispatch to
  compute, persist, `log_event` on create/delete.
- Schemas — `SelfEmploymentCalculationCreate` (request + optional `borrower_id`,
  `label`) and `SelfEmploymentCalculationResponse` (with `breakdown`).
- `app/routers/self_employment_calculations.py` — case-scoped `POST/GET/GET-by-id/
  DELETE` under `/cases/{case_id}/self-employment-calculations`; map `CaseNotFound` /
  `SelfEmploymentCalculationNotFound` → 404, `InvalidSelfEmploymentInput` → 422.
  Register in `main.py`.
- Case summary: add `self_employment_calculations` to
  `case_summary_builder.build_case_summary` and add their `annual_income` to the
  total **alongside the employment / rental / non-taxable totals** (same documented
  additive + double-count caveat). Add it to `CaseSummaryResponse`; fetch it (scoped)
  in `result_service.get_case_summary`.

Tests (mirror the non-taxable ones): service (persist/compute for a personal and an
entity kind, scoping, manager access, list/get/delete, missing/cross-case
not-found); summary additive total (incl. a negative self-employment calc reducing
it); integration (401, create then in summary total, cross-broker 404, scoped list,
delete 204).

## Part C — Frontend (commit separately)

Mirror the non-taxable UI, but the form is larger — **drive it from a per-kind field
config** (a data structure describing each kind's components/fields and their year
layout) rendered generically, rather than eight hand-written forms. Keep components
small.

- `frontend/src/api/income.ts` — add `calculateSelfEmployment`,
  `saveSelfEmploymentCalculation(caseId, payload)`,
  `listSelfEmploymentCalculations(caseId)`,
  `deleteSelfEmploymentCalculation(caseId, id)`; add types.
- A self-employment worksheet page: pick `kind`, then render that kind's fields
  (personal schedules show one subtotal's line items per year; entities show the K-1 /
  W-2 / business-return components with ownership % on the business return, and
  dividends for corp). Up to two years with months + include toggles. Preview shows
  the qualifying monthly + breakdown; "Save to case" persists with an optional label.
- On `CaseDetailPage`, add a "Self-employment income" panel listing saved calcs
  (label, kind, monthly, annual) with delete. The summary total already reflects them.
- Frontend tests (vitest): preview (a schedule and an entity), save, list/delete.

## Out of scope
- No extraction, no `Result`/pipeline changes, no editing saved calcs (create +
  delete only), no dedupe vs. streams, no Liquidity/Comparative/P&L tabs.

## Workflow & definition of done
- Backend: `pytest` fully green. Frontend: `npm run test` + `npm run build` pass.
  Commit+push each part.
- One model/endpoint set with registry dispatch handles all eight kinds; new table via
  `create_all`; scoping enforced; exceptions mapped; self-employment losses flow
  through negative into the summary; files within size limits; no dead code.
- A broker can compute a Schedule C and a partnership, save them to a case, see them
  listed, watch the summary total move (including downward for a loss), and delete them.
- Add a line to `PROGRESS.md`/`TODO.md`: self-employment wired + persisted + in case
  summary — **all three Excel workbooks now fully replicated and surfaced end-to-end**;
  next = printable-worksheet output (populate the .xlsx templates), then revisit the
  blank-line-item-defaults-to-0 question across the self-employment forms.
