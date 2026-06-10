# Claude Code task — Self-employment engine, part 2: entities (partnership / S-corp / corp)

## Before you start

Read in full:

1. `AGENTS.md` — follow every rule (income logic isolated in `app/income/`, pure
   functions, named exceptions, files < ~175 lines — split by concern, one
   responsibility per file, every module tested, commit/push per validated set, keep
   `PROMPT.md` out of commits).
2. `docs/income-engine-spec.md` — **sections 5.3, 5.4, 5.5, and 5.6** are the
   authority for this task.
3. **Part 1 is your template — mirror it.** `app/income/self_employment.py`,
   `app/income/self_employment_schedules.py`,
   `app/schemas/self_employment_inputs.py`, and
   `tests/unit/test_self_employment_personal*.py`. Match the shape (per-line subtotal
   formulas in one file, the months-weighted averaging in another, dataclass results,
   tie-out tests) and use the **same field/validation conventions** as part 1 so the
   two are consistent.

This is the **pure calc engine only** — no extraction, DB, routes, or persistence.
Do not touch `income_service.py`, the pipeline, routers, or part-1 behavior.

## Goal

Build the deterministic engine for the three business-entity types — Partnership
(1065 + K-1), S-Corporation (1120S + K-1), Corporation (1120) — each producing a
qualifying monthly figure that ties out to the `All-In-One` SAM/Summary sheets to the
cent (spec 5.3–5.6).

## The key structural difference from part 1

A personal schedule had one annual subtotal. An **entity has multiple components**,
each independently averaged across two years (months-weighted, spec 5.6) and then
**summed**:

- **Partnership:** `K-1 subtotal` + `W-2 wages (Box 5)` + `Form 1065 share`
- **S-Corp:** `K-1 subtotal` + `W-2 wages (Box 5)` + `Form 1120S share`
- **Corporation:** `W-2 wages (Box 5)` + `Form 1120 share` (no K-1)

**Ownership % applies ONLY to the business-return component** (1065 / 1120S / 1120) —
never to the K-1 (already the borrower's share) or W-2 (the borrower's own wages).
The Corporation additionally **subtracts dividends paid to the borrower** from its
share. Reuse the part-1 months-weighted averaging helper rather than duplicating it
(promote it to a shared location if it's currently private).

## Scope — build exactly this

- `app/schemas/self_employment_entity_inputs.py` — Pydantic inputs, each component
  holding up to two years with `months` (default 12) + `included`, per spec 5.3–5.5:
  - K-1 (partnership): ordinary_income (L1), net_rental_income (L2&3),
    guaranteed_payments (L4c).
  - K-1 (S-corp): ordinary_income (L1), net_rental_income (L2&3).
  - W-2 wages: wages (Box 5).
  - Form 1065 year: passthrough_other_partnerships (L4), nonrecurring_income
    (L5/6/7), depreciation (L16c), depreciation_8825 (L14), depletion (L17),
    amortization_casualty_nonrecurring_loss, mortgages_notes_payable_lt_1yr
    (Sch L L16 d), travel_entertainment_exclusion (Sch M-1 L4b), ownership_pct.
  - Form 1120S year: nonrecurring_income (L4/5), depreciation (L14),
    depreciation_8825 (L14), depletion (L15), amortization_casualty_nonrecurring_loss,
    mortgages_notes_payable_lt_1yr (Sch L L17 d), travel_entertainment_exclusion
    (Sch M-1 L3b), ownership_pct.
  - Form 1120 year: taxable_income (L30), total_tax (L31),
    nonrecurring_gains_losses (L8/9), nonrecurring_income (L10), depreciation (L20),
    depletion (L21), amortization_casualty_nonrecurring_loss,
    nol_and_special_deductions (L29a/b), mortgages_notes_payable_lt_1yr (Sch L L17 d),
    travel_entertainment_exclusion (Sch M-1 L5c), ownership_pct,
    dividends_paid_to_borrower (1040 Sch B L5).
  - Three entity wrappers: `PartnershipInput` (k1_years, w2_years, form_1065_years),
    `SCorpInput` (k1_years, w2_years, form_1120s_years),
    `CorporationInput` (w2_years, form_1120_years).
- `app/income/self_employment_entity_subtotals.py` — the per-year **annual subtotal**
  formulas implementing spec 5.3–5.5 exactly:
  - `k1_partnership_subtotal`, `k1_s_corp_subtotal`
  - `form_1065_subtotal`, `form_1120s_subtotal`, `form_1120_subtotal`
  - the **share** = `business_subtotal * ownership_pct`; for the Corporation,
    `form_1120_subtotal * ownership_pct - dividends_paid_to_borrower` (per year).
  Losses (negative) pass through unclamped.
- `app/income/self_employment_entity.py` — the engine:
  - `compute_partnership`, `compute_s_corporation`, `compute_corporation`, each
    averaging every component across its years (months-weighted, reusing the part-1
    helper) and summing the component monthlies into the entity qualifying monthly.
  - Return a dataclass with `qualifying_monthly`, `entity_type`, and a per-component
    breakdown (component name, its monthly, per-year detail) for review.
  - Mirror Excel `IFERROR(...,0)` divide-by-zero guards; round to 2 decimals where
    the spec marks.

## Exceptions
Reuse `InvalidSelfEmploymentInput` for missing required fields (same convention as
part 1).

## Tests — `tests/unit/test_self_employment_entity.py` (split if large)
AAA, descriptive names, fast/isolated. Tie-out cases computed by hand from spec 5.3–5.5:

- Partnership: K-1 (incl. guaranteed payments) + W-2 + (1065 subtotal × ownership);
  verify the 1065 add-backs and the two subtractions (mortgages < 1yr, T&E exclusion).
- S-Corp: K-1 (no guaranteed payments) + W-2 + (1120S subtotal × ownership).
- Corporation: W-2 + (1120 subtotal × ownership − dividends paid); verify
  taxable_income − total_tax and the NOL/special-deductions add-back.
- **Ownership % applies only to the business return** — prove K-1 and W-2 are
  unscaled by it.
- Component independence: a component (or a year) toggled off drops out; multi-year
  months-weighted averaging; a loss passes through negative; zero-months guard;
  missing-field validation raises `InvalidSelfEmploymentInput`.

## Out of scope
- No personal-schedule changes (part 1). No Liquidity / Comparative / P&L tabs.
- No extraction, DB, routes, persistence, or summary wiring (that's the combined
  self-employment wire+persist slice next). No changes to other engines.

## Workflow & definition of done
- `pytest` fully green (new tests pass; nothing existing breaks). Commit+push.
- Files follow AGENTS.md; the averaging helper is shared, not duplicated.
- Ties out to spec 5.3–5.5 to the cent; ownership-% scoping, the corp dividend
  subtraction, component independence, and loss pass-through each proven by a test.
- Add a line to `PROGRESS.md`/`TODO.md`: self-employment entity engine landed; all
  Form 1084 calc logic now built; next = wire + persist self-employment (personal +
  entity) into preview/save/case-summary, then the printable-worksheet output decision.
