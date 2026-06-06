# Claude Code task — Non-taxable income & Social Security engine

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule. Especially: income logic isolated in
   `app/income/`, pure functions with injected inputs (no file/DB/network), named
   domain exceptions, files < ~175 lines, one responsibility per file, every module
   tested (AAA, unhappy paths), commit/push per validated set, keep `PROMPT.md` out
   of commits.
2. `docs/income-engine-spec.md` — **section 3 (Non-taxable income & Social Security)**
   and section 1.3 (gross-up rate) are the authority. Implement exactly that.
3. The engines you are mirroring for structure/style:
   `app/income/rental.py` + `app/schemas/rental_inputs.py` and their tests
   (`tests/unit/test_rental_income.py`). Match that shape: Pydantic input models, a
   pure engine returning dataclasses, tie-out tests.

This task is the **pure calc engine only** — no extraction, DB, routes, or
persistence (those come in a later wire+persist slice, mirroring rental). Do not
touch `income_service.py`, the pipeline, or routers.

## Goal

Build the deterministic non-taxable income + Social Security qualifying engine that
ties out to the `Income-Worksheet` "Non-taxable Income" tab to the cent (spec
section 3). The gross-up rate is 25% (spec 1.3), passed as a parameter defaulting to
`0.25`.

## Scope — build exactly this

- `app/schemas/nontaxable_inputs.py` — Pydantic input models:
  - **Non-taxable income** with a `method` (one of three, spec 3):
    - `gross_100` — uses `annual_gross`
    - `total_adjusted` — uses `annual_gross` + `annual_taxable`
    - `current_monthly` — uses `current_monthly` + `annual_gross` + `annual_taxable`
      (the return's taxable ratio is applied to the current monthly amount)
    plus `gross_up_rate: float = 0.25`.
  - **Social Security** with a `method` (two, spec 3): `gross_100` (uses
    `annual_gross`) or `adjusted` (gross + 15% of gross × 25%), uses `annual_gross`.
- `app/income/nontaxable.py` — the engine:
  - `compute_nontaxable_income(source) -> NonTaxableResult` implementing the three
    methods exactly per spec 3:
    - gross_100: `round(annual_gross / 12, 2)`
    - total_adjusted: `round(taxable/12, 2) + round((gross - taxable) * (1+rate) / 12, 2)`
    - current_monthly: `taxable_mo = current_monthly * (taxable/gross)`,
      `eligible_mo = current_monthly - taxable_mo`,
      `round(taxable_mo + eligible_mo * (1+rate), 2)`
  - `compute_social_security(ss) -> NonTaxableResult` per spec 3:
    - gross_100: `round(annual_gross / 12, 2)`
    - adjusted: `round((annual_gross + annual_gross * 0.15 * 0.25) / 12, 2)`
  - Return a dataclass with the qualifying `monthly` figure plus a small reviewable
    breakdown (method used, and the taxable/eligible split where relevant).
  - Guard divide-by-zero (e.g. `current_monthly` method when `annual_gross` is 0) the
    Excel `IFERROR(...,0)` way — return 0 for the ratio, don't crash.
  - Round to 2 decimals at the points the spec marks, matching Excel.

## Exceptions
Add `InvalidNonTaxableInput` to `app/exceptions.py`; raise it for a method missing
its required fields (e.g. `total_adjusted` without `annual_taxable`). No raw
`ValueError`, no silent excepts.

## Tests — `tests/unit/test_nontaxable_income.py`
AAA, descriptive names, fast/isolated. Tie-out cases (compute expected by hand from
spec 3, assert to the cent):

- gross_100: e.g. `$24,000` annual → `$2,000.00` monthly.
- total_adjusted: a gross with a partial taxable portion; verify the non-taxable
  slice is grossed up 25% and the taxable slice is not.
- current_monthly: verify the taxable ratio from the return is applied to the
  current monthly amount before gross-up.
- Social Security gross_100 and adjusted (verify the `gross + gross*0.15*0.25` form).
- Divide-by-zero guard (current_monthly with zero gross → 0, no crash).
- Each missing-field validation error raises `InvalidNonTaxableInput`.

## Out of scope
- No extraction, DB, routes, persistence, or summary wiring (later slice).
- No multi-source aggregation here — the engine computes one source; summing across
  sources is a wiring concern handled later.
- No rental / employment / self-employment changes.

## Workflow & definition of done
- `pytest` fully green (new tests pass; nothing existing breaks). Commit+push.
- Files follow AGENTS.md (size, one responsibility, named exception, no dead code).
- Ties out to the spec section 3 examples to the cent, with all three non-taxable
  methods and both Social Security methods each proven by a test.
- Add a line to `PROGRESS.md`/`TODO.md`: non-taxable engine landed; next = wire +
  persist non-taxable (mirroring rental), then self-employment (Form 1084 — needs
  SAM rows 113–443 transcribed into spec section 5 first).
