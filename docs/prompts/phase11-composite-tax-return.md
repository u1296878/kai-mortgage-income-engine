# Claude Code task — Make a tax return a composite source (no AGI double-count)

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. Commit in the parts below.
Reuse the existing engines and the `schedule_e_rental_service` draft pattern — do not
reimplement calc logic.

## Problem

A 1040 contains several income types (wages, Schedule C, Schedule E). Today,
`tax_return` does three things, two of them wrong:
1. Creates per-property **rental drafts** from Schedule E — correct (keep).
2. Saves the result's `annual_income = AGI` (`income_service` tax_return branch).
   AGI is a *tax* figure, not qualifying income, **and** it already includes the
   rental net — so it both mis-states income and **double-counts** the rental drafts
   in the case summary.
3. Extracts `schedule_c_net` but never turns it into a self-employment draft, so
   self-employment income from the return is dropped.

Goal: a tax return fans out into reviewable **per-schedule qualifying drafts**
(rental [done] + self-employment [new]); AGI/total income become display-only
cross-checks and never enter the case total.

## Part A — Retire AGI-as-income for tax returns (fixes the double-count)

- In `app/services/income_service.py` (and/or `result_service.save_extraction_result`),
  a `tax_return` result must contribute **no** income to the case summary: set its
  `annual_income = None` (so `summarize_case_income`, which already skips `None`,
  ignores it). Keep `agi`, `total_income`, and `wages` as extracted fields (with their
  source boxes) for display/cross-check, and add a `notes` value like
  "Income derived from per-schedule drafts; AGI shown for reference only."
- Test: a case with a `tax_return` result + rental drafts totals only the drafts (AGI
  is not added; no double-count).

## Part B — Schedule C → self-employment drafts (new)

Mirror `app/services/schedule_e_rental_service.py` with a self-employment equivalent.

- Extend the Schedule C extraction (in `tax_return_extractor` / a `schedule_c`
  extractor using the `tax_return_locator` helpers + `schedule_c_pages`) to pull the
  Form 1084 add-back lines per Schedule C business, not just net profit:
  net_profit (L31), nonrecurring_income (L6), depletion (L12), depreciation (L13),
  meals_entertainment_exclusion (L24b), business_use_of_home (L30),
  business_miles (Part IV L44a) + the return's tax year (for the mileage rate),
  amortization_casualty. Schedule C is single-column (one business per Schedule C
  page) — handle multiple Schedule C businesses if present.
- New `app/services/schedule_c_se_service.py`: from those fields build a
  `ScheduleCInput` (one `ScheduleCYear`, `months=12`, `tax_year` set), run the
  engine via the existing dispatch (`compute_schedule_c` / `KIND_REGISTRY`), and
  create `SelfEmploymentCalculation` drafts (`kind="schedule_c"`, `included=True`,
  `source_document_id`, a source key per business, dedup by source like the rental
  service). Call it from `job_processing_service` for `tax_return` documents,
  alongside the existing rental-draft call.
- Test (synthetic fields): a Schedule C with add-backs produces a self-employment
  draft whose qualifying monthly matches `compute_schedule_c`, and it appears in the
  case summary; dedup prevents duplicate drafts on reprocess.

## Part C — Wages: reference only (no misleading employment draft)

Surface 1040 wages (line 1) as an extracted reference field, but do **not** auto-create
an employment draft from it — employment qualifying needs paystub/W-2 period data
(months-weighted blend), which a 1040 annual figure can't provide. Add a `notes` /
UI hint telling the broker to add employment via the paystub/W-2 worksheet. (Leave a
TODO for a future "wages → employment draft needing verification" if desired.)

## Part D — UI clarity (`frontend`)

Update the document-type help text so it reflects the real behavior:
- `tax_return`: "Extracts rental (Schedule E) and self-employment (Schedule C) income
  as reviewable drafts. AGI/total income are shown for reference only and are not added
  to the total."
- `other`: keep its current meaning, but if it still uses the old net-only rental
  extractor, note that standalone Schedule E rental should prefer the tax_return path
  (or wire `other` to the same draft creation in a later pass — out of scope here).

## Part E — Tests / PII
Do NOT commit real tax-return PDFs (they contain SSNs/names). Use synthetic
`blocks`/fields fixtures mirroring a 1040 with Schedule C and Schedule E.

## Out of scope
- No change to the rental engine, the self-employment engines, or the manual
  worksheets. No ownership auto-detection (broker include/excludes drafts). No
  reworking of `other` beyond the help text.

## Definition of done
- `pytest` green; `npm run test`/`build` pass. Commit per part.
- Uploading a 1040 with rental + Schedule C produces rental **and** self-employment
  drafts the broker can include/exclude; the case total sums only the included drafts
  (plus any separately-uploaded W-2/paystub/bank results); **AGI is never added**.
  Note in PROGRESS/TODO that tax returns are now composite and AGI-as-income is retired.
