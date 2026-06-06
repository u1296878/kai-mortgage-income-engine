# Claude Code task — Wire the employment engine end-to-end (stateless slice)

## Before you start

Read in full:

1. `AGENTS.md` — the rules. Follow every one. Especially: layer order
   (Router → Service → Repository/engine), no business logic in route handlers,
   named domain exceptions, files under ~175 lines, one responsibility per file,
   every module has tests, commit/push per validated change set, keep `PROMPT.md`
   out of commits.
2. `docs/income-engine-spec.md` — section 2 (employment) is the calc authority.
3. The engine you are wiring: `app/income/employment.py`,
   `app/schemas/income_inputs.py`, `app/income/pay_frequency.py`.
4. Pattern references to imitate: `app/routers/cases.py` (auth via
   `Depends(get_current_user)`, mapping domain exceptions to `HTTPException`),
   `app/services/case_service.py`, and the frontend `frontend/src/api/cases.ts`
   + `frontend/src/pages/CaseDetailPage.tsx`.

## Goal

Make the employment qualifying-income engine usable end-to-end: an authenticated
broker fills in a worksheet-style form, the backend runs the existing engine, and
the per-bucket breakdown + total monthly qualifying income render on screen.

**This slice is stateless** — compute and return, no persistence. Rationale: the
`Result` model is bound to a job + document (both non-null) and does not fit a
manually-entered worksheet. Persisting the result and wiring it into the case
summary is the next slice; do NOT attempt it here. Do not modify the `Result`
model, the extraction pipeline, or `income_service.py` in this task.

---

## Part A — Backend (do first; commit when green)

Create:

- `app/schemas/income_results.py` — Pydantic response models mirroring the engine's
  dataclasses (`PeriodResult`, `BucketResult`, `EmploymentResult`) so the engine
  stays pure (keeps returning dataclasses) and the API has a typed contract.
- `app/services/employment_income_service.py` — thin service: takes an
  `EmploymentInput`, calls `compute_employment_income`, maps the dataclass result to
  the response model, emits a `log_event`. No DB, no file/network access.
- `app/routers/income.py` — `APIRouter(prefix="/income")`, one route:
  `POST /income/employment/calculate`. Requires `get_current_user`. Body is
  `EmploymentInput`; response is the employment result response model.
  Map `InvalidEmploymentInput` → `HTTPException(status_code=422, ...)` following the
  existing router exception-mapping style (`raise ... from error`).
- Register the router in `app/main.py` alongside the others.

Tests:

- `tests/unit/test_employment_income_service.py` — service delegates to the engine
  and returns the mapped response (assert on outcomes, real engine, no mocking what
  we own).
- `tests/integration/test_income_router.py` — at minimum:
  - 401 when unauthenticated,
  - 200 happy path returning the correct total + per-bucket breakdown,
  - 422 when the A/Y toggle rule is violated (both set / neither set),
  - 422 on a malformed body (Pydantic validation).

Reuse the existing auth/test fixtures used by other integration tests
(`tests/integration/`) — match how they register/log in a broker.

## Part B — Frontend (do after Part A is green; commit separately)

Create a worksheet-style form so the slice is demoable in the UI:

- `frontend/src/api/income.ts` — `calculateEmploymentIncome(input)` calling
  `POST /api/income/employment/calculate` via the existing `client.ts`.
- Add request/response types to `frontend/src/types/api.ts`.
- A page (e.g. `frontend/src/pages/EmploymentIncomePage.tsx`) routed under the
  authenticated app shell and linked from the nav. It collects:
  - Base pay: up to three periods (date from / through / total earnings, include
    toggle) + an optional rate-of-pay line (rate, pay frequency dropdown, hours/week
    when hourly, include toggle).
  - Overtime, Bonus, Commission, Other: up to three periods each + an A/Y toggle.
  On submit, call the API and render each bucket's qualifying monthly figure, the
  per-period monthly + % change, and the total.
- Keep components small (AGENTS.md applies to the frontend too) — factor out a
  period-rows subcomponent and a variable-bucket subcomponent rather than one large
  file.
- Pay-frequency dropdown options must match the backend keys exactly: `hourly`,
  `weekly`, `biweekly`, `semimonthly`, `monthly`, `quarterly`, `semiannually`,
  `annually`, `varies`.

Frontend test (vitest, like the existing `*.test.tsx`):

- `EmploymentIncomePage.test.tsx` — fills the form, submits with the API client
  mocked, asserts the returned total renders.

## Out of scope (do NOT do here)

- No persistence, no new DB models/columns, no migrations, no case-summary
  integration. (That is the next slice.)
- No changes to `Result`, the extraction pipeline, `income_service.py`, or the
  worker.
- No auto-extraction of worksheet values from documents.
- No rental, non-taxable, or self-employment work.

## Workflow & definition of done

- Backend: `pytest` fully green (new tests pass, nothing existing breaks). Commit+push.
- Frontend: `npm run test` and `npm run build` pass. Commit+push.
- Domain exception mapped correctly; routes require auth; files within AGENTS.md
  size limits; no dead code.
- A broker can log in, open the form, enter worksheet values, and see the computed
  qualifying monthly breakdown and total.
- Add a short line to `PROGRESS.md`/`TODO.md`: employment engine wired end-to-end
  (stateless); next slice = persist the result and fold it into the case summary.
```
