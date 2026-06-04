# Claude Code task — Employment qualifying-income engine

## Before you start

Read these in full before writing any code:

1. `AGENTS.md` — the rules for this codebase. They do not bend. Follow every one.
2. `docs/income-engine-spec.md` — the income engine spec. **Section 2 (Employment)**
   and **Section 1 (Shared concepts)** are the authority for this task. Implement
   exactly what they describe.
3. `app/services/income_service.py` and `app/schemas/extraction.py` — the current
   income code you are extending alongside (do not delete it in this task).

## Goal

Build the **pure, deterministic employment qualifying-income calculation engine**
that ties out to the company's Excel worksheet (`Income-Worksheet`) to the cent.
This task is the calc core only — no extraction, no DB, no routes. Those come later.

## Scope — build exactly this

Create, matching the layout in spec section "Proposed code layout":

- `app/income/__init__.py`
- `app/income/dates.py` — `months_between(date_from, date_through) -> float`
  per spec 1.1 (fractional months, including partial first/last month).
- `app/income/pay_frequency.py` — the pay-frequency table (spec 1.2) and a
  `rate_of_pay_monthly(...)` helper (spec 2.2).
- `app/schemas/income_inputs.py` — the Pydantic input models from spec 2.5
  (`EmploymentPeriod`, `VariableBucket`, `BasePay`, `EmploymentInput`).
- `app/income/employment.py` — the engine:
  - per-period monthly earnings + `% change` (spec 2.1)
  - months-weighted blend per bucket (spec 2.2) — **this is a weighted blend
    `Σearnings / Σmonths`, NOT an average of period monthlies**
  - base-pay rate-of-pay line added to the blend (spec 2.2)
  - the Annualize (A) vs YTD (Y) toggle for variable buckets (spec 2.3),
    including the both-set / both-unset validation error
  - total qualifying monthly income (spec 2.4)
  - return per-bucket figures AND the total, so the breakdown is reviewable

Tests (mirror source structure under `tests/unit/`):

- `tests/unit/test_income_dates.py`
- `tests/unit/test_pay_frequency.py`
- `tests/unit/test_employment_income.py`

## Hard constraints (from AGENTS.md — call-outs)

- **Income logic in one place.** Everything goes in `app/income/`. Nothing else
  does income math. Do not scatter calculations.
- **Keep files small.** Under 150 lines, hard cap 175. Split if approaching it.
- **One responsibility per file.** dates, pay frequency, and the employment engine
  are separate files.
- **Explicit over implicit.** Pure functions; pass inputs in; no global state, no
  hidden imports inside functions, no file/DB/network access in this engine.
- **Named domain exceptions.** Add any new failure modes (e.g. the A/Y validation
  error — propose `InvalidEmploymentInput`) to `app/exceptions.py`. Do not raise
  raw `ValueError`/`Exception` for domain errors. No silent `except: pass`.
- **`pathlib.Path`** for any path (none expected here, but the rule stands).
- **No dead code, no unused imports.** Delete, don't comment out.
- **Rounding must match Excel.** Round to 2 decimals at the points the spec marks.
  Mirror Excel's `IFERROR(...,0)` guards (e.g. divide-by-zero → 0, not a crash).

## Testing requirements (from AGENTS.md)

- Every module has a test file. Behavioral tests against the public interface only.
- Arrange / Act / Assert, in that order, blank-line separated. Descriptive names
  (`test_blend_weights_by_months_not_simple_average`, not `test_1`).
- Unit tests are fast and isolated — no DB, filesystem, or network (this engine
  has none, so keep it that way).
- **Tie-out tests:** include at least one golden case per bucket whose expected
  qualifying figure you computed from the worksheet logic in the spec, and assert
  the engine matches to the cent.
- Cover unhappy paths: missing prior year, missing dates, zero months
  (divide-by-zero guard), and the A/Y both-set and both-unset validation errors.
- Include `months_between` cases for full calendar years, partial months, a leap
  year (e.g. Feb 2024), and cross-year ranges. Verify the spec's worked examples
  (`2025-01-01`→`2025-12-31` = 12.0; `2026-01-01`→`2026-04-15` = 3.5).

## Out of scope (do NOT do in this task)

- No document parsing or extractor changes.
- No DB models, repositories, routers, or services wiring.
- No self-employment (Form 1084), rental, or non-taxable income — employment only.
- Do not rip out `income_service.py` yet; it is replaced in a later task once the
  engine is wired in.

## Workflow

- Run `pytest` and get the full suite green before considering the task done. New
  tests pass; you have not broken existing ones.
- Follow the commit/push cadence in AGENTS.md: commit and push each validated
  change set to GitHub. Keep `PROMPT.md` out of commits.
- Keep commits scoped and messages clear.

## Definition of done

- All five source files and three test files exist and follow AGENTS.md.
- The engine ties out to the spec's employment examples to the cent.
- Weighted-blend, rate-of-pay, and A/Y toggle behavior are each proven by a test.
- `pytest` is fully green. Changes committed and pushed.
- Briefly note in `PROGRESS.md`/`TODO.md` that the employment calc engine landed
  and what remains (extraction wiring, then rental / non-taxable / self-employment).
