# Tie-out findings

Discrepancies between the engine and the real Excel worksheets, found by recalculating
the actual files under LibreOffice and comparing to the engine. See
`docs/verification/tie-out-plan.md` for method and `tests/tieout/fixtures/` for data.

## F1 - Employment: per-period months must be rounded to 2 dp before blending (resolved)

**Severity:** real mismatch on any fractional-month period.

**Status:** resolved by the F1 employment rounding fix.

Excel's "# of months" column is `I{n} = ROUND(J{n}, 2)`, and the qualifying blend
divides by `SUMIF(... I{n})`, so it sums the **rounded** month counts. The engine's
`months_between` returns full precision and `employment._blend` divides by the
unrounded sum.

Example (`partial_month_fractional` fixture): YTD 2026-01-01 to 01-15 ($2,500) plus
2025 full ($60,000). Months = 15/31 = 0.483871. Excel uses 0.48 and returns
**$5,008.01**; the engine uses 0.483871 and returns **$5,006.46**.

**Resolution:** `app/income/employment.py` now rounds each period's months to 2 dp
before the weighted blend, matching `I{n} = ROUND(months, 2)`. Whole-month periods are
unaffected, so the 8 other employment scenarios still tie out. The
`partial_month_fractional` fixture now runs as a normal passing regression.

## F2 - Employment: base rate-of-pay and base period rows are mutually exclusive (enforce/UI)

**Severity:** minor; not wrong for valid inputs, but the engine is more permissive
than the worksheet.

The worksheet validation `Q12` ("If this line is checked, the three below cannot be")
forbids using the base-pay **rate-of-pay line** together with the base **period rows**.
The engine's `_base_pay` adds `rate_of_pay_monthly + blend` unconditionally, so it
would over-count if a caller supplied both.

**Fix (low priority):** enforce mutual exclusivity by either raising
`InvalidEmploymentInput` when `rate_line_included` and any base period is included, or
preventing it in the worksheet UI. No change needed for inputs that already use just
one.

## F3 - Self-employment: months denominator must agree (convention / wiring)

**Severity:** none for the engine; a wiring/UI consistency requirement.

The All-In-One `Summary` defaults each entity row to 12 months per year (24 total).
The engine divides by the **included** years' months. For a **single-year**
self-employment entry, the two only agree if the empty year is dropped on the Excel
side, which is what the engine already does.

Verified: the `schedule_c_mileage_1yr` fixture ties out ($4,441.67) only with the
Summary's year 2 excluded. **No engine change.** The wiring/UI must set per-year
`months`/`included` so a single-year entry uses 12, and a saved calc records which
years are included.

## F4 - All engines require line items explicitly; Excel treats blank as 0 (decision)

**Severity:** low; usability, not correctness.

Excel treats a blank cell as 0. The engines currently require each line item and raise
on `None`. The tie-out fixtures therefore supply explicit `0`s for every unused field.
This is fine for correctness but means the API/UI must send full payloads.

**Decision to make (not in this pass):** default the line-item fields to `0.0` so
blanks behave like the spreadsheet, or keep them required and have the UI send zeros.

## F5 - Self-employment: entity component rounding differs by one cent (engine review)

**Severity:** low; one-cent mismatch in a two-year corporation scenario.

The `corporation_dividends_2yr` fixture recalculates to **$6,916.67** in Excel and
the engine returns **$6,916.66**. The likely root cause is rounding order: the engine
rounds each component monthly figure before summing the entity total, while the
worksheet appears to carry fractional component monthlies into the final total and
then round the sum.

**Fix (not in the F1 pass):** review self-employment entity aggregation rounding
against the Summary sheet and decide whether to sum unrounded component monthly values
before the final entity round. This is recorded as a strict xfail so the harness stays
honest without broadening the F1 fix.

---

## Summary of tie-out results (18 scenarios)

| Worksheet | Scenarios | Tie out | Discrepancy |
|---|---|---|---|
| Employment | 9 | 9 | F1 resolved |
| Rental | 4 | 4 | none |
| Self-employment | 5 | 4 | **F5** (entity component rounding); F3 is a denominator convention handled in fixtures |

F1 is resolved. F2/F3/F4 are conventions/usability notes; F5 should be reviewed in a
separate self-employment rounding pass. Per instructions, the harness keeps remaining
discrepancies recorded for later, deliberate fix passes.
