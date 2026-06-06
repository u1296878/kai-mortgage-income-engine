# Claude Code task — Rental qualifying-income engine

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule. Especially: income logic isolated in one place
   (`app/income/`), pure functions with injected inputs (no file/DB/network),
   named domain exceptions, files under ~175 lines, one responsibility per file,
   every module has tests (AAA, cover unhappy paths), commit/push per validated
   change set, keep `PROMPT.md` out of commits.
2. `docs/income-engine-spec.md` — **section 4 (Rental)** and section 1 (shared
   concepts) are the authority for this task. Implement exactly what they describe.
3. The employment engine you are mirroring for structure/style:
   `app/income/dates.py`, `app/income/employment.py`,
   `app/schemas/income_inputs.py`, `tests/unit/test_employment_income.py`.
   Match that shape: Pydantic input models, a pure engine returning dataclasses,
   tie-out tests.

This task is the **pure calc engine only** — no extraction, no DB, no routes, no
persistence. Those come in later slices (mirroring how employment was wired then
persisted). Do not touch `income_service.py`, the extraction pipeline, or routers.

## Goal

Build the deterministic rental qualifying-income engine that ties out to the
company's `Rental-Worksheet` to the cent (spec section 4).

## Scope — build exactly this

- `app/schemas/rental_inputs.py` — Pydantic input models (keep rental inputs in
  their own file; don't overload `income_inputs.py`). Cover:
  - A Schedule-E year entry: `months_in_service` (default 12, capped at 12),
    `rents_received`, `total_expenses`, `insurance`, `mortgage_interest`, `taxes`,
    `depreciation_depletion`, `hoa_addback`, `casualty_one_time`.
  - A property with: `property_class` (`primary_2_4_unit` | `investment`),
    `method` (`schedule_e` | `lease`), up to two Schedule-E years, optional
    `monthly_pitia` (investment), and lease fields (`gross_monthly_rent` =
    the lesser of lease vs. appraisal market rent — caller supplies the lesser;
    `vacancy_factor` default `0.25`).
- `app/income/rental.py` — the engine:
  - `months_from_fair_rental_days(days) -> float` helper: `min(days / 30, 12)`,
    defaulting to 12 when days are missing (spec 4.1).
  - **Schedule-E annual net** per year (spec 4.1):
    `rents - total_expenses + insurance + mortgage_interest + taxes +
    depreciation_depletion + hoa_addback + casualty_one_time`.
    Rental **losses are legitimate** — negative annual net must pass through, not
    clamp to zero. Mirror Excel `IFERROR(...,"N/A"/0)` only for divide-by-zero
    (zero months → guard, don't crash).
  - **Primary residence (2–4 unit):** report gross. Two-year average is
    **annual-weighted**: `(annual_y1 + annual_y2) / (months_y1 + months_y2)`.
  - **Investment property:** per year `net_monthly = annual_net/months -
    monthly_pitia`; two-year average is **months-weighted on net**:
    `(months_y1*net_y1 + months_y2*net_y2) / (months_y1 + months_y2)`.
    (Note the two classes use different averaging — primary averages annual gross,
    investment averages net monthly. Get both right; spec 4.1.)
  - **Lease method** (spec 4.2): `adjusted_monthly = gross_monthly_rent *
    (1 - vacancy_factor)`. For an **investment** property under the lease method,
    also subtract `monthly_pitia` to yield net. Primary residence does not subtract
    PITIA.
  - Return a dataclass result with the qualifying monthly figure plus a reviewable
    breakdown (per-year annual net + monthly, and the method/class used), the way
    `employment.py` returns per-bucket detail.
  - Round to 2 decimals at the points the spec marks, matching Excel.
- `tests/unit/test_rental_income.py` — behavioral tie-out tests.

If `rental_inputs.py` or `rental.py` approaches the 175-line cap, split by concern
(e.g. a small `rental_results.py` for the dataclasses).

## Exceptions
Reuse a named domain exception for invalid rental input if needed; add one to
`app/exceptions.py` (e.g. `InvalidRentalInput`) rather than raising raw
`ValueError`. No silent excepts.

## Testing requirements
AAA, descriptive names, fast/isolated (no DB/fs/network). Include tie-out cases:

- Primary residence Schedule E, two years, annual-weighted average.
- Investment Schedule E with `monthly_pitia` subtracted, months-weighted net average.
- Lease method primary (gross × 0.75) and investment (× 0.75 then minus PITIA).
- A rental **loss** (negative annual net) flows through as negative — not zeroed.
- `months_from_fair_rental_days`: `300/30 = 10`, `>360 days` caps at 12, missing → 12.
- Single year only (missing prior year); zero-months divide-by-zero guard.

Compute each expected qualifying figure by hand from the spec formulas and assert to
the cent.

## Out of scope
- No extraction, DB, routes, persistence, or case-summary wiring (later slices).
- No self-employment or non-taxable work. No changes to `income_service.py`.
- No multi-property aggregation/total here — the engine computes one property;
  summing across properties is a wiring concern handled later.

## Workflow & definition of done
- `pytest` fully green (new tests pass; nothing existing breaks). Commit+push.
- Files follow AGENTS.md (size, one responsibility, named exceptions, no dead code).
- The engine ties out to the spec's rental examples to the cent, with primary vs.
  investment averaging and the lease vacancy factor each proven by a test.
- Add a line to `PROGRESS.md`/`TODO.md`: rental calc engine landed; next = wire +
  persist rental (mirroring employment), then the non-taxable engine.
