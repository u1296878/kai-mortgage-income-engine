# Income engine tie-out verification plan

Purpose: prove the rules-based engine matches the company's **actual Excel
worksheets** to the cent, end to end — not just the formulas as transcribed into the
spec, but against the source files themselves.

## Approach (automated, oracle = the real Excel files)

The Excel files recalculate under **LibreOffice headless**, so the comparison can be
automated rather than done by hand:

```
for each scenario:
  1. copy the worksheet, write the scenario's inputs into the known input cells (openpyxl)
  2. recalc:  soffice --headless --calc --convert-to xlsx --outdir <out> <file>
  3. read the qualifying output cell from the recalc'd file (openpyxl data_only=True)
  4. run the same scenario through the engine
  5. assert engine == excel, exact to the cent ($0.00 tolerance)
```

This was validated in the sandbox: LibreOffice recalculated the real
`Income-Worksheet` for the scenarios below and every figure matched the engine
formula exactly.

> Where to run it: the **Excel side** (steps 1–3) runs anywhere LibreOffice is
> installed. The **engine side** (step 4) needs the app deps, so the full assertion
> harness should live in the repo and run in Claude Code / CI where `pytest` runs.
> Split cleanly: a script generates an Excel-oracle **fixtures file**
> (`scenario → inputs + excel_expected`); a pytest module asserts the engine matches
> each fixture.

## Already validated (sandbox, LibreOffice vs engine formula)

| Rule exercised | Inputs | Excel | Engine |
|---|---|---|---|
| Base pay months-weighted blend | YTD 2026-01-01→04-15 = $17,500 (3.5 mo) + 2025 full = $60,000 | $5,000.00 | $5,000.00 |
| Variable bucket, YTD method (Y) | OT $6,000 over 3 mo | $2,000.00 | $2,000.00 |
| Variable bucket, annualize (A) | OT $6,000, months forced to 12 | $500.00 | $500.00 |
| Non-taxable gross-up (total adjusted) | gross $30,000, taxable $18,000 | $2,750.00 | $2,750.00 |
| Social Security adjusted | gross $24,000 | $2,075.00 | $2,075.00 |

## Coverage matrix (every tricky rule needs ≥1 scenario)

Legend: ✅ validated above · ⬜ to run.

Employment:
- ✅ months-weighted blend (≠ simple average) · ✅ A/Y toggle (both states)
- ⬜ rate-of-pay (hourly = rate×hours×52/12; non-hourly = rate×freq/12)
- ⬜ three-period blend (YTD + 2 prior years) · ⬜ partial-month fractional period
- ⬜ declining income (negative % change still blends)

Non-taxable:
- ✅ total-adjusted gross-up · ✅ SS adjusted
- ⬜ gross-100% method · ⬜ current-monthly method (taxable ratio applied)

Rental:
- ⬜ primary 2–4 unit, Schedule E, 2-year annual-weighted average
- ⬜ investment, Schedule E, PITIA subtracted, months-weighted net average
- ⬜ lease method (25% vacancy) · ⬜ rental loss (negative) · ⬜ partial months (fair-rental-days/30)

Self-employment:
- ⬜ Schedule C sole prop (add-backs) · ⬜ Schedule C single-member LLC (W-2 add)
- ⬜ Schedule C mileage (year rate) · ⬜ Schedule B / D / E-royalty / F (one each)
- ⬜ Partnership (K-1 + W-2 + 1065 share × ownership) · ⬜ S-corp · ⬜ Corporation (− dividends)
- ⬜ business loss (negative) · ⬜ ownership-% applies only to the business return

## Input-cell maps

### Income-Worksheet → `Primary Employment` (confirmed)
Per income bucket, three period rows (YTD, prior, prior-prior). Base pay = rows
14/15/16; Overtime = 23/24/25; Bonus = 32/33/34; Commission = 41/42/43; Other =
52/53/54. For each period row N: `F{N}` date-from, `G{N}` date-through, `H{N}` total
earnings, `R{N}` include checkbox (boolean True/False). Base pay rate-of-pay line:
`R12` include, `G12` rate, `H12` pay-frequency (dropdown text), `I12` hours/week.
Variable buckets' A/Y toggle: `R22/S22` (OT), `R31/S31` (Bonus), `R40/S40` (Comm),
`R51/S51` (Other) — A = R, Y = S.
Outputs: base `K18`, OT `K27`, bonus `K36`, commission `K45`, other `K56`,
**total `K59`**.

### Income-Worksheet → `Non-taxable Income` (confirmed)
Block 1 rows 7–17: `H7` annual gross, `H8` taxable; method include checkboxes `R7`
(gross 100%), `R10` (total adjusted), `R12` (current monthly, with `L12` monthly
amount), `R15`. Output `K17`. SS block rows 39–43: `H39` gross, `R39` (gross 100%) /
`R41` (adjusted). Output `K43`. (Blocks 2–4 repeat at +16/… row offsets.)

### Rental-Worksheet (to confirm before first run)
`Investment Property` / `Principal Residence (2-4 Unit)`: year inputs in column `I`
(year 1) and `L` (year 2); per property block, Schedule E lines: months, rents,
total expenses, insurance, mortgage interest, taxes, depreciation/depletion, HOA,
casualty (rows per the sheet), annual gross, monthly, PITIA (investment), net,
average. Outputs: investment **avg net `J26`** (first block); primary **avg gross
`J24`**. Lease block: gross monthly rent, vacancy `H65`=0.25, adjusted `J66`. Set the
`$I$4` / `$L$4` year inputs. Confirm exact rows against the file before the run.

### All-In-One → `SAM` + `Summary` (to confirm before first run)
Enter line items into `SAM` (column `I` = year 1, `L` = year 2) per spec 5.2–5.5.
Subtotals: Schedule C `I30`; partnership 1065 `I142`; S-corp 1120S `I270`; corp 1120
`I389`; etc. The `Summary` tab converts to monthly per row and sums at `K58`.
**Watch the months denominator:** Summary defaults each year to 12 (total 24). The
engine divides by the *included* years' months. For a single-year self-employment
case, either give both years in both, or exclude the empty year / set months in the
Summary so the two denominators agree — otherwise a one-year case will look like a
50% mismatch. This convention check is itself a valuable tie-out result.

## Harness implementation (recommended)

1. `scripts/tieout/excel_oracle.py` — given a scenarios file (inputs + cell map per
   worksheet), fills cells, recalcs via LibreOffice, writes
   `tests/tieout/fixtures/<worksheet>.json` (`scenario_id → {inputs, excel_expected}`).
   Pin the source `.xlsx` versions and record them in the fixtures (a worksheet
   revision can change a formula).
2. `tests/tieout/test_<worksheet>_tieout.py` — load the fixtures, build the engine
   input from each scenario's `inputs`, assert
   `engine_total == excel_expected` exactly (round to 2 dp both sides).
3. Run the oracle step whenever the worksheets change; run the assertion tests in CI.

## Caveats / watch-list
- **Cell-mapping fragility** — verify each map against the actual file before trusting
  a "mismatch"; a wrong cell ref looks like an engine bug.
- **Blank vs 0** — Excel treats a blank cell as 0; the self-employment engine
  currently *requires* each line item. Make scenarios supply explicit 0s (or decide
  to default the engine fields to 0) so the two agree.
- **Months denominator** in self-employment (see SAM note above).
- **File versions** — pin and record the worksheet revision used for each fixture.

## Suggested order
Employment (extend to full coverage) → Non-taxable (finish) → Rental → Self-employment.
Self-employment last: most scenarios and the months-denominator nuance to settle.
