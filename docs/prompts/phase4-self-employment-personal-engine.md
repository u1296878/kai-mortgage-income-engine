# Claude Code task — Self-employment engine, part 1: personal schedules (B/C/D/E/F)

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule. Especially: income logic isolated in
   `app/income/`, pure functions with injected inputs (no file/DB/network), named
   domain exceptions, files < ~175 lines (this is large — split by concern), one
   responsibility per file, every module tested (AAA, unhappy paths), commit/push per
   validated set, keep `PROMPT.md` out of commits.
2. `docs/income-engine-spec.md` — **section 5, specifically 5.2 and 5.6** are the
   authority for this task. Section 5.3–5.5 (partnership / S-corp / corp) are the
   NEXT task — do not build them here.
3. The engines you are mirroring for structure/style: `app/income/rental.py`,
   `app/income/nontaxable.py` and their input schemas + tests. Match that shape:
   Pydantic input models, a pure engine returning dataclasses, tie-out tests.

This task is the **pure calc engine only** — no extraction, DB, routes, or
persistence (a wire+persist slice follows once both self-employment parts exist). Do
not touch `income_service.py`, the pipeline, or routers.

## Goal

Build the deterministic engine for the **personal** Fannie Mae 1084 schedules —
Schedule B, C (incl. single-member LLC), D, E (royalties on 1040), and F (farm) —
each producing an annual cash-flow subtotal and a qualifying monthly figure, tying
out to the `All-In-One` SAM sheet to the cent (spec 5.2).

## Scope — build exactly this

- `app/schemas/self_employment_inputs.py` — Pydantic input models, one per schedule,
  each holding up to two tax years with a `months` field (default 12) and an
  `included` flag per year, plus the line items from spec 5.2. Specifically:
  - Schedule B: recurring interest, recurring dividends.
  - Schedule C: net_profit (L31), nonrecurring_income (L6), depletion (L12),
    depreciation (L13), meals_entertainment_exclusion (L24b), business_use_of_home
    (L30), business_miles + `tax_year` (to pick the mileage rate),
    amortization_casualty. Add an optional `w2_self_employment_income` (Box 5) field
    used for the **single-member LLC** variant (0/None for a plain sole prop).
  - Schedule D: recurring_capital_gains (L16).
  - Schedule E (royalties/other on 1040): royalty_income (L4), total_expenses (L20),
    depreciation_depletion (L18). **Name it distinctly** (e.g.
    `ScheduleERoyaltyYear`) — `rental_inputs.py` already defines a `ScheduleEYear`
    for rental properties; do not collide or conflate the two.
  - Schedule F (farm): net_profit (L34), nontax_coop_ccc_payments, nonrecurring_loss,
    nonrecurring_income, depreciation (L14), amortization_casualty_depletion,
    business_use_of_home.
- `app/income/self_employment.py` — the engine (split into a second file if it nears
  the size cap, e.g. `self_employment_schedules.py` for the per-schedule annual-subtotal
  formulas and `self_employment.py` for averaging/aggregation):
  - A per-schedule **annual subtotal** function implementing each formula in spec 5.2
    exactly. Losses (negative subtotals) are legitimate and must pass through unclamped.
  - **Mileage depreciation** = `business_miles * rate(tax_year)` where the
    depreciation portion of the standard mileage rate is **2025 = 0.33, 2024 = 0.30,
    2023 = 0.28** (a small lookup; raise on an unknown year, or treat as 0 only if
    miles are 0). Single-member LLC adds `w2_self_employment_income` to the Schedule C
    subtotal (spec 5.2).
  - A **two-year average** to qualifying monthly, months-weighted exactly like the
    Summary (spec 5.6): `qualifying_monthly = sum(included annual subtotals) /
    sum(included months)`. A year toggled off drops its subtotal and its months.
  - Each engine entry computes **one** schedule (e.g. one Schedule C business) →
    one result dataclass with per-year subtotals + the qualifying monthly. Summing
    across multiple businesses/schedules is a wiring concern handled later.
  - Mirror Excel `IFERROR(...,0)` for divide-by-zero (zero months → 0).
  - Round to 2 decimals where the spec marks, matching Excel.

## Exceptions
Add `InvalidSelfEmploymentInput` to `app/exceptions.py` for missing required fields
or an unknown mileage year. No raw `ValueError`, no silent excepts.

## Tests — `tests/unit/test_self_employment_personal.py`
AAA, descriptive names, fast/isolated. Tie-out cases (compute expected by hand from
spec 5.2, assert to the cent):

- Schedule C sole prop: a year with depreciation/depletion/BUOH added back and
  nonrecurring income + meals exclusion subtracted; verify the subtotal.
- Schedule C **single-member LLC**: same plus `w2_self_employment_income` added.
- **Mileage**: `business_miles * 0.33` for 2025, `* 0.30` for 2024; unknown year
  behavior per your rule.
- Schedule B, D, E (royalty), F each: one tie-out case.
- **Two-year months-weighted average** to monthly; a year excluded drops out.
- A **loss** (negative subtotal) passes through negative; zero-months guard; each
  missing-field validation error raises `InvalidSelfEmploymentInput`.

## Out of scope
- No partnership / S-corp / corporation (spec 5.3–5.5) — that is the next prompt.
- No Liquidity / Comparative / P&L tabs (advisory, not qualifying income — spec note).
- No extraction, DB, routes, persistence, or summary wiring. No changes to
  `income_service.py` or other engines.

## Workflow & definition of done
- `pytest` fully green (new tests pass; nothing existing breaks). Commit+push.
- Files follow AGENTS.md (size, one responsibility, named exception, no dead code);
  the Schedule-E naming collision with rental is avoided.
- Ties out to the spec 5.2 examples to the cent; mileage, single-member LLC, the
  two-year average, and loss pass-through each proven by a test.
- Add a line to `PROGRESS.md`/`TODO.md`: self-employment personal schedules
  (B/C/D/E/F) engine landed; next = the entity engine (partnership/S-corp/corp, spec
  5.3–5.6), then wire + persist self-employment.
