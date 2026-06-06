# Income Engine Specification

Source of truth for porting the company's qualifying-income rules into the
refactor. Derived from the three production worksheets:

- `Income-Worksheet-Macro-Free.xlsx` — employment + non-taxable income
- `Rental-Worksheet-Macro-Free.xlsx` — rental income
- `All-In-One-Worksheet-Macro-Free.xlsx` — self-employment (Fannie Mae Form 1084 cash-flow)

These are standard Fannie Mae / Freddie Mac (Enact-style) MI income worksheets.
Every number a borrower qualifies on traces back to one of the formulas below.

## Design principles

1. **Deterministic, rules-based, no LLM.** Every figure here is arithmetic on
   documented inputs. This matches AGENTS.md ("rules over LLM") and the goal of a
   cheaper engine now, with AI extraction added later as an optional front-end.
2. **The calc engine is pure and ties out to the sheets cent-for-cent.** It takes
   explicit worksheet line-items as input and returns qualifying monthly income.
   No file I/O, no DB, no extraction inside it. Extraction is a separate layer that
   *populates* these inputs and can improve independently.
3. **Rounding matches Excel.** Round to 2 decimals at the points the sheets round
   (noted per formula). Getting rounding order right is required to tie out.
4. **All qualifying income is expressed monthly.** Annual figures are derived
   only for display.

## Proposed code layout (refactor)

AGENTS.md requires income logic isolated in one place, files under ~175 lines,
pure functions with injected inputs. Suggested structure:

```
app/income/
    dates.py            # months_between(from_date, through_date) -> float
    pay_frequency.py    # PAY_FREQUENCY table + monthly rate-of-pay
    employment.py       # base/OT/bonus/commission/other qualifying income
    nontaxable.py       # gross-up + social security
    rental.py           # Schedule E + lease method
    self_employment.py  # Form 1084 per-entity cash flow  (largest; phase 2)
app/schemas/
    income_inputs.py    # Pydantic input models per income type
```

Extractors (`app/extractors/`) produce structured fields; a thin service maps
those fields onto these input models and calls the pure calc functions. The
existing `app/services/income_service.py` is replaced by calls into `app/income/`.

---

# 1. Shared concepts

## 1.1 Months between two dates (fractional)

Every employment period and rental period needs a precise month count, including
partial months at each end. The sheets compute it as (Excel `K` column):

```
months(F, G) =
    whole_months_strictly_between(F, G)
  + first_month_fraction(F)
  + last_month_fraction(G)

whole_months_strictly_between(F, G) =
    (year(G) - year(F)) * 12 - 12 + (12 - month(F)) + month(G) - 1

first_month_fraction(F) = (days_in_month(F) - day(F) + 1) / days_in_month(F)
last_month_fraction(G)  = day(G) / days_in_month(G)
```

Worked check: `F = 2025-01-01`, `G = 2025-12-31`
→ whole = 0 - 12 + 11 + 12 - 1 = 10; first = 31/31 = 1; last = 31/31 = 1; **total = 12.0**. Correct.

Worked check: `F = 2026-01-01`, `G = 2026-04-15`
→ whole = 0 - 12 + 11 + 4 - 1 = 2; first = 31/31 = 1; last = 15/30 = 0.5; **total = 3.5**.

Python reference implementation:

```python
from calendar import monthrange
from datetime import date

def months_between(f: date, g: date) -> float:
    whole = (g.year - f.year) * 12 - 12 + (12 - f.month) + g.month - 1
    f_days = monthrange(f.year, f.month)[1]
    g_days = monthrange(g.year, g.month)[1]
    first = (f_days - f.day + 1) / f_days
    last = g.day / g_days
    return whole + first + last
```

## 1.2 Pay frequency table

From the `Support` sheet (`VLKP_PAY_FREQ`). Used for rate-of-pay base income.

| Selection        | Periods/year |
|------------------|--------------|
| Hourly (H)       | special (see 2.2) |
| Weekly (52)      | 52 |
| Bi-Weekly (26)   | 26 |
| Semi-Monthly (24)| 24 |
| Monthly (12)     | 12 |
| Quarterly (4)    | 4 |
| Semi-Annually (2)| 2 |
| Annually (1)     | 1 |
| Varies           | 0 (rate-of-pay not usable) |

## 1.3 Gross-up rate

Non-taxable gross-up rate = **25%** (multiply eligible non-taxable income by 1.25).

---

# 2. Employment income  (BUILD FIRST)

Worksheet: `Income-Worksheet` → `Primary Employment`. Five independent buckets:
**Base Pay, Overtime, Bonus, Commission, Other Income**. Each is analyzed over up
to three periods: YTD (current year, 2026), prior year (2025), prior-prior (2024).

## 2.1 Per-period monthly earnings

For each period the underwriter enters: `date_from`, `date_through`,
`total_earnings`, and an include flag. Then:

```
months        = months_between(date_from, date_through)        # section 1.1
monthly       = round(total_earnings / months, 2)
pct_change    = (monthly - prior_period_monthly) / abs(prior_period_monthly) * 100
```

`pct_change` is **informational only** — it flags rising/declining trends for
underwriter judgment. It does not change the qualifying number. Surface it; don't
auto-act on it (declining-income exclusion is a manual decision).

## 2.2 Qualifying income per bucket

The qualifying figure is a **months-weighted blend**, NOT a simple average of the
period monthlies:

```
qualifying_monthly(bucket) =
    round( sum(total_earnings for selected periods)
           / sum(months for selected periods), 2 )
```

This weights each period by how many months it represents. (E.g. a full year and a
3-month YTD blend as `(year_total + ytd_total) / (12 + 3)`, not `(year_monthly + ytd_monthly) / 2`.)

**Base Pay** additionally allows a rate-of-pay line, added to the blend:

```
rate_of_pay_monthly =
    (rate * hours_weekly * 52) / 12     if frequency == Hourly
    (rate * periods_per_year) / 12      otherwise

qualifying_base = round( (rate_of_pay_monthly if rate line selected else 0)
                         + blend_of_selected_periods, 2 )
```

## 2.3 Annualize (A) vs YTD (Y) toggle  — variable buckets only

OT / Bonus / Commission / Other have an A/Y toggle on the YTD row:

- **Y (default):** YTD months = `months_between(date_from, date_through)` (actual).
- **A (annualize):** YTD months is forced to **12** (treat the YTD total as a
  full-year figure → divides by 12 in the blend).
- Exactly one of A/Y must be set; both-set or both-unset is a validation error.

Base Pay has no A/Y toggle.

## 2.4 Total qualifying employment income

```
total_monthly = qualifying_base + qualifying_overtime + qualifying_bonus
              + qualifying_commission + qualifying_other
```

## 2.5 Input model (employment)

```python
class EmploymentPeriod(BaseModel):
    date_from: date
    date_through: date
    total_earnings: float
    included: bool = True

class VariableBucket(BaseModel):           # OT, bonus, commission, other
    periods: list[EmploymentPeriod]        # YTD, prior, prior-prior
    annualize_ytd: bool = False            # True = "A", False = "Y"

class BasePay(BaseModel):
    periods: list[EmploymentPeriod]
    rate: float | None = None
    pay_frequency: str | None = None       # key into PAY_FREQUENCY
    hours_weekly: float | None = None
    rate_line_included: bool = False

class EmploymentInput(BaseModel):
    base_pay: BasePay
    overtime: VariableBucket
    bonus: VariableBucket
    commission: VariableBucket
    other: VariableBucket
```

## 2.6 Gap vs. current refactor

`income_service.compute_annual_income` currently returns W-2 box wages or pay-stub
YTD ÷ current calendar month — neither uses period dates, months-weighting,
rate-of-pay, or the A/Y toggle, and the pay-stub path annualizes on `datetime.now()`
rather than the document dates (a correctness bug, see project review). The
extractors must be extended to capture, per bucket, `date_from`, `date_through`,
and `total_earnings` so the engine above can run.

---

# 3. Non-taxable income & Social Security

Worksheet: `Income-Worksheet` → `Non-taxable Income`. Pick **one** method per source.

**Method A — gross amount, 100% (no gross-up):**
```
monthly = round(annual_gross / 12, 2)
```

**Method B — total adjusted from tax return (gross-up the non-taxable portion):**
```
eligible_nontaxable = gross - taxable
monthly = round(taxable / 12, 2) + round((eligible_nontaxable * 1.25) / 12, 2)
```

**Method C — current monthly amount, prorated by the return's taxable ratio:**
```
taxable_ratio = taxable / gross
taxable_mo    = current_monthly * taxable_ratio
eligible_mo   = current_monthly - taxable_mo
monthly       = round(taxable_mo + eligible_mo * 1.25, 2)
```

**Social Security without taxation documentation** (pick one):
```
# 100% gross:
monthly = round(gross_annual / 12, 2)
# adjusted (15% of gross grossed up at 25%):
monthly = round((gross_annual + gross_annual * 0.15 * 0.25) / 12, 2)
```

---

# 4. Rental income

Worksheet: `Rental-Worksheet`. Two property classes; two methods each.

## 4.1 Schedule E method (existing property with tax history)

```
months_in_service = min(fair_rental_days / 30, 12)     # default 12 if days missing

annual_net = rents_received            # Sch E Line 3
           - total_expenses            # Line 20
           + insurance                 # Line 9
           + mortgage_interest         # Lines 12 + 13
           + taxes                     # Line 16
           + depreciation_depletion    # Line 18
           + hoa_addback               # only if itemized on Sch E
           + casualty_one_time         # one-time extraordinary, with evidence

monthly_gross = annual_net / months_in_service
```

**Primary residence (2–4 unit)** stops at gross. Two-year average (annual-weighted):
```
avg_monthly = (annual_net_y1 + annual_net_y2) / (months_y1 + months_y2)
```

**Investment property** subtracts PITIA to get net, then averages net (months-weighted):
```
net_monthly_y = monthly_gross_y - monthly_pitia
avg_net = (months_y1 * net_monthly_y1 + months_y2 * net_monthly_y2)
          / (months_y1 + months_y2)
```

## 4.2 Lease method (new acquisition, no tax history)

```
vacancy_factor = 0.25
adjusted_monthly_rent = gross_monthly_rent * (1 - vacancy_factor)
# gross_monthly_rent = lesser of lease rent or appraisal market rent
```

> Rental income reported by a *business* on IRS Form 8825 is NOT calculated here —
> it goes through the self-employment engine (section 5).

---

# 5. Self-employment (Form 1084 cash-flow)  — PHASE 2

Worksheet: `All-In-One` → `SAM` (engine) + `Summary` (aggregation). This replicates
Fannie Mae Form 1084. Each entity yields a two-year cash-flow subtotal; the Summary
converts to monthly and sums included entities.

## 5.1 Summary aggregation

```
qualifying_monthly(entity) = (subtotal_y1 + subtotal_y2) / total_months   # default 24, adjustable
total_self_employment = sum(qualifying_monthly for included entities)
```

## 5.2 Per-schedule subtotals (annual, per year)

**Schedule B — interest & dividends:** `recurring_interest + recurring_dividends`.

**Schedule C — sole proprietor (Line refs on 1040 Sch C):**
```
subtotal = net_profit_L31
         - nonrecurring_income_L6
         + depletion_L12
         + depreciation_L13
         - meals_entertainment_exclusion_L24b
         + business_use_of_home_L30
         + mileage_depreciation
         + amortization_casualty_if_noted
```
*Single-member LLC* additionally adds `w2_income_from_self_employment` (W-2 Box 5).

**Mileage depreciation** = `business_miles * rate(year)` where the depreciation
portion of the standard mileage rate is: **2025 = $0.33, 2024 = $0.30, 2023 = $0.28**.
(Note: the legacy `kai_*.xlsx` LOOKUPS table held stale 2020–2022 rates; use these.)

**Schedule D — capital gains:** `recurring_capital_gains_L16` (only if recurring).

**Schedule E (on 1040) — royalties/other:**
```
subtotal = royalty_income_L4 - total_expenses_L20 + depreciation_depletion_L18
```

**Schedule F — farm:**
```
subtotal = net_profit_L34
         + nontax_coop_ccc_payments
         + nonrecurring_loss
         - nonrecurring_income
         + depreciation_L14
         + amortization_casualty_depletion_if_noted
         + business_use_of_home_if_noted
```

For the three entity types below, the borrower's annual income (per year) is the sum
of three independently-averaged components: (1) the Schedule K-1 subtotal, (2) W-2
wages paid to the borrower (Box 5), and (3) the business return's cash-flow share
**after** multiplying by ownership %. The ownership-% multiplier applies **only** to
the business-return portion — the K-1 is already the borrower's share and W-2 is the
borrower's own wages. (Corporations have no K-1 component.)

> Judgment flag (not a calc change): when K-1 ordinary/net-rental income exceeds
> distributions, investors may require evidence the business can support the
> withdrawal (liquidity). Surface it; don't alter the number.

### 5.3 Partnership — Form 1065 + Schedule K-1
```
k1_subtotal = ordinary_income_K1_L1
            + net_rental_income_K1_L2_3
            + guaranteed_payments_K1_L4c

form_1065_subtotal = passthrough_income_loss_other_partnerships_L4
                   - nonrecurring_income_L5_6_7
                   + depreciation_L16c
                   + depreciation_form_8825_L14
                   + depletion_L17
                   + amortization_casualty_nonrecurring_loss
                   - mortgages_notes_payable_lt_1yr        # Sch L, L16, col d
                   - travel_entertainment_exclusion        # Sch M-1, L4b
partner_share = form_1065_subtotal * ownership_pct

entity_annual = k1_subtotal + w2_wages_box5 + partner_share
```

### 5.4 S Corporation — Form 1120S + Schedule K-1
```
k1_subtotal = ordinary_income_K1_L1 + net_rental_income_K1_L2_3   # no guaranteed pmts

form_1120s_subtotal = - nonrecurring_income_L4_5
                      + depreciation_L14
                      + depreciation_form_8825_L14
                      + depletion_L15
                      + amortization_casualty_nonrecurring_loss
                      - mortgages_notes_payable_lt_1yr       # Sch L, L17, col d
                      - travel_entertainment_exclusion       # Sch M-1, L3b
shareholder_share = form_1120s_subtotal * ownership_pct

entity_annual = k1_subtotal + w2_wages_box5 + shareholder_share
```

### 5.5 Corporation — Form 1120
```
form_1120_subtotal = taxable_income_L30
                   - total_tax_L31
                   + nonrecurring_gains_losses_L8_9     # deduct gains / add losses
                   - nonrecurring_income_L10
                   + depreciation_L20
                   + depletion_L21
                   + amortization_casualty_nonrecurring_loss
                   + nol_and_special_deductions_L29a_b
                   - mortgages_notes_payable_lt_1yr      # Sch L, L17, col d
                   - travel_entertainment_exclusion      # Sch M-1, L5c
corp_share = form_1120_subtotal * ownership_pct - dividends_paid_to_borrower   # 1040 Sch B L5

entity_annual = w2_wages_box5 + corp_share
```

### 5.6 Entity aggregation (Summary tab)
Each component line (K-1, W-2, each business return) is independently averaged across
the two years and divided by its month count (default 12 per year, 24 total), with a
per-line, per-year exclude toggle, then summed:
```
qualifying_monthly(entity)  = sum(component monthly figures, included only)
total_self_employment       = sum(qualifying_monthly for included entities)
```
The worksheet provides up to 4 partnerships, 4 S-corps, 3 corporations, plus the
personal Schedule B/C/D/E/F. Mirror Excel `IFERROR(...,0)` guards throughout.

> The All-In-One workbook also has Liquidity, Comparative, and P&L analysis tabs.
> Those are advisory/trend analysis, **not** part of the qualifying-income number —
> out of scope for the calc engine (revisit only if the company wants them).

---

# 6. Testing strategy (tie-out)

Per AGENTS.md (behavioral tests, AAA, cover unhappy paths):

1. **Golden tie-out cases.** For each income type, build input fixtures with known
   worksheet outputs (fill the Excel sheet, read the qualifying figure, assert the
   engine returns the same to the cent). Start with employment.
2. **`months_between` unit tests** for full years, partial months, leap years,
   cross-year ranges.
3. **Weighted-blend tests** proving blend ≠ naive average when period lengths differ.
4. **A/Y toggle tests** including the both-set / both-unset validation errors.
5. **Edge cases:** zero/negative net (rental loss, Sch C loss), missing prior year,
   missing dates, division-by-zero guards (Excel uses `IFERROR(...,0)` — mirror it).

# 7. Build order

1. `dates.months_between` + tests
2. `pay_frequency` table + rate-of-pay
3. `employment` engine + tie-out tests   ← first deliverable
4. `nontaxable` (gross-up + SS)
5. `rental` (Schedule E + lease)
6. Wire extractors → input models for employment (capture period dates/earnings)
7. `self_employment` — Schedule B/C/D/E/F + partnership/S-corp/corp (section 5 now
   fully transcribed; the largest engine — consider splitting per entity type)
```
