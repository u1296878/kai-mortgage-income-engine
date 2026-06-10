# Document tie-out — David Hendrickson (Schedule C self-employment)

> **Re-test #3 — commit `a2bf82b`, now validated against the REAL `All-In-One`
> worksheet (LibreOffice recalc as oracle).** Three findings, cleanly separated:
>
> **1. The income MATH engine is correct — ties out to the worksheet to the cent.**
> Filling the real `All-In-One` sheet with the Hendrickson Schedule C line items and
> recalculating under LibreOffice gives:
>
> | | 2023 | 2024 |
> |---|---|---|
> | `SAM!I30` / `L30` subtotal | 102,641 | 89,079 |
> | `Summary!K8` qualifying monthly | — | **$7,988.33** ((102,641+89,079)/24) |
>
> `compute_schedule_c` on the same inputs returns subtotals **102,641 / 89,079** and
> **$7,988.33/mo** — exact match. The engine's Schedule C formula and the worksheet
> formula (`I30 = I19 − I20 + SUM(I21:I22) − I23 + I24 + mileage + I28`, mileage rates
> 2023=.28/2024=.30) are identical. **No math discrepancy.**
>
> **2. The extraction layer is still broken — so end-to-end the engine produces $0.**
> The column-aware Schedule C extractor still returns no line items on either real
> return (the `_amount_column_band` ±10pt row-match to line 31 fails — see Re-test #2
> below). With no `net_profit` extracted, no self-employment draft is created, so the
> correct $7,988.33 never gets produced from the actual PDFs. **The entire failure is
> in extraction, not the calculation.**
>
> **3. Responsiveness fix landed and works.** The `Index tax return extraction lookups`
> commit cut full 30-page scanned-return extraction from a >80s timeout to **~0.5s**.
> `Bound OCR page processing` and `Expose job progress status` are also in. The latency
> problem is resolved.
>
> **Bottom line:** if extraction is fixed to pull L31/L6/L12/L13/L24b/L30/miles/amort,
> the engine will return $7,988.33 — the exact worksheet figure. That one extraction
> bug is the only thing standing between the engine and a correct tie-out for this
> borrower.
>
> ---

> **Re-test #2 after commit `8886ecf` "Add column-aware Schedule C extraction" —
> still does not tie out, now in a new way: the engine extracts NO Schedule C line
> items at all, so it produces no self-employment income for either return.**
>
> | Field | 2023 correct | 2023 @8886ecf | 2024 correct | 2024 @8886ecf |
> |---|---|---|---|---|
> | total_income (1040) | 94,380 | ✅ 94,380 | 85,247 | ✅ 85,247 |
> | schedule_c_net (1040 routing) | 94,380 | ✅ 94,380 | 85,247 | ✅ 85,247 |
> | Sch C net_profit / depreciation / home / etc. | — | ❌ **none extracted** | — | ❌ **none extracted** |
> | Qualifying monthly | $8,553.42 | **not computed** | $7,423.25 | **not computed** |
>
> Progress vs `3427840`: the 1040 top-line regression is fixed (total_income correct
> again), and the line-27a add-back is now correctly scoped — it only adds Part V items
> whose label contains "amortization"/"casualty" (here: $0, which is right). Good design.
>
> **But the new column-aware extractor extracts nothing on a real Schedule C.** Root
> cause, confirmed on both the digital (2023) and OCR (2024) returns:
> `schedule_c_columns._amount_column_band` anchors the amount column by finding the
> line-"31" marker and requiring a money value within `ROW_TOLERANCE = 10` points of that
> marker's row. On an actual 1040 Schedule C the line-31 amount sits vertically offset
> from the "31" digit (the label wraps over several rows and the value is on the brace
> row). No money falls within ±10 pt of the "31" block → `band` is `None` → `line_amount_value`
> returns `None` for **every** line → zero Schedule C fields → no `net_profit` → the
> self-employment draft is never created.
>
> Debug (both docs): `schedule_c_pages = [8]`, line-31 block found at x≈36–41 / y≈640,
> `band = None`.
>
> Likely fix direction: don't gate the whole amount column on a tight row-aligned match
> to line 31. Establish the amount band from the right-edge money column across the page
> (or widen/relax the row tolerance and match the value on the brace row), then read each
> line's value from that band. Re-run these two returns as the test.
>
> ---

> **Re-test #1 after commit `3427840` "Fix Schedule C extraction addbacks" — STILL FAILS,
> and the digital path regressed badly.** The original run below was against `0d57aa9`.
>
> | | 2023 correct | 2023 @0d57aa9 | 2023 @3427840 | 2024 correct | 2024 @0d57aa9 | 2024 @3427840 |
> |---|---|---|---|---|---|---|
> | Monthly | **$8,553.42** | $8,250.67 | **−$2,629.42** 💥 | **$7,423.25** | $7,788.83 | $7,839.67 |
> | Subtotal | 102,641 | 99,008 | −31,553 | 89,079 | 93,466 | 94,076 |
>
> What the fix did:
> - ✅ **Bug B fixed** — line 27a is no longer added back as amortization/casualty
>   (2024 `amortization_casualty` is now 0, was $5,046).
> - ❌ **Bug A not fixed** — line 13 depreciation still wrong: 0 on 2024 (should be 659);
>   on 2023 it now grabs **$10,959**, which is line 23 *Taxes and licenses*, not depreciation.
> - 💥 **New regression — `business_use_of_home` now reads `8,829`** on *both* documents:
>   it is picking up the form reference "Form **8829**", not the line-30 dollar amount
>   (should be 4,628 / 3,173).
> - 💥 **New regression (digital 2023 only)** — `nonrecurring_income` (line 6) now reads
>   **$145,721** (that's line 1/7 gross receipts), and `total_income` reads **$6,742**
>   (a Schedule 1 adjustments figure, not the $94,380 total). Subtracting the bogus
>   $145,721 is what drives the −$2,629/mo result.
>
> Net: 2024 is about the same distance off as before ($+416 vs $+366); 2023 went from
> slightly low to catastrophically negative. The `tax_return_locator` anchor changes in
> this commit broke more than they fixed. Detail below is from the original `0d57aa9` run.

---


Ran two borrower returns through the **live engine** (parse → `extract_tax_return_fields`
→ `compute_schedule_c`) and compared to the correct Form 1084 cash-flow figures read
from the source documents. Borrower is a sole proprietor (attorney), Schedule C only.

- **2023 return** — digital PDF, parsed by `pdf_parser`.
- **2024 return** — scanned PDF (no text layer), parsed by `ocr_parser` (Tesseract).

## Verdict

**Both documents fail to tie out.** The income figure is wrong on each, for two
distinct engine defects. The errors happen to push in opposite directions, so the
2-year average looks close (+$31/mo) even though neither year is right.

| | 2023 | 2024 |
|---|---|---|
| Correct qualifying subtotal (annual) | **$102,641** | **$89,079** |
| Engine subtotal (annual) | $99,008 | $93,466 |
| Correct monthly (subtotal ÷ 12) | **$8,553.42** | **$7,423.25** |
| Engine monthly | $8,250.67 | $7,788.83 |
| Monthly error | **−$302.75 (low)** | **+$365.58 (high)** |
| Correct 2-yr avg monthly | **$7,988.33** | |
| Engine 2-yr avg monthly | $8,019.75 (+$31.42) | |

## Extraction scorecard (field-by-field)

Correct values read from the source returns (2024 verified visually off the scan).

| Sch C line | Field | 2023 correct | 2023 engine | 2024 correct | 2024 engine |
|---|---|---|---|---|---|
| 31 | Net profit | 94,380 | ✅ 94,380 | 85,247 | ✅ 85,247 |
| 13 | Depreciation/§179 | 3,633 | ❌ **missed (0)** | 659 | ❌ **missed (0)** |
| 30 | Business use of home | 4,628 | ✅ 4,628 | 3,173 | ✅ 3,173 |
| 12 | Depletion | 0 | ✅ 0 | 0 | ✅ 0 |
| 24b | Meals exclusion | 0 | ✅ 0 | 0 | ✅ 0 |
| 6 | Nonrecurring (other) income | 0 | ✅ 0 | 0 | ✅ 0 |
| 44a | Business miles | 0 | ✅ 0 | 0 | ✅ 0 |
| 27a | "Other expenses" → amortization/casualty add-back | 0 *(none qualify)* | ✅ not added | 0 *(none qualify)* | ❌ **added $5,046** |

## Two confirmed defects

### Bug A — line 13 depreciation is never extracted (both docs)
The Schedule C extractor (`schedule_c_extractor.MONEY_LINES["depreciation"] =
("13", ("depreciation",))`) failed to capture the value on both returns. On this form
the line 13 label ("Depreciation and section 179 expense deduction…") wraps across
several rows and the amount sits well to the right / vertically offset, so the
`nearest_money_value` heuristic returns nothing. Depreciation is a standard,
always-applied 1084 add-back, so missing it understates income by the full line-13
amount every time ($3,633/yr in 2023, $659/yr in 2024).

### Bug B — line 27a is added back wholesale as "amortization/casualty" (fired on 2024)
The extractor maps `amortization_casualty = line 27a` (the **total** "Other expenses").
Per Fannie Mae Form 1084, only the *amortization or casualty-loss* portion inside
"Other expenses" is added back — not the whole line. Here line 27a is entirely
ordinary costs:
- 2023 Part V: bank fees 77, business fee 31, computer/software 759, telephone 2,690,
  other 4,000 = **7,557** — none is amortization or casualty.
- 2024 Part V: accounting 100, bank charges 3,487, telephone 1,459 = **5,046** —
  none is amortization or casualty.

The correct add-back is **$0** in both years. The engine added the full $5,046 on the
2024 (OCR) doc, overstating that year. On the 2023 (digital) doc the extractor happened
not to find line 27a at all, so it wasn't added — meaning the engine is also
**inconsistent** between the digital and scanned paths.

## Notes
- Net profit, business-use-of-home, depletion, meals, and miles all extracted
  correctly on both the digital and scanned documents — OCR itself read the key
  numbers fine.
- The wired path (`schedule_c_se_service`) builds **one year per document**
  (subtotal ÷ 12). The 2-year average shown above is computed by hand for reference;
  the combined averaging lives in a higher aggregation layer not exercised here.
- Sandbox caveat: the repo files were partially cloud-synced, so the engine modules
  were reconstructed from `git HEAD` (0d57aa9) to run. Results reflect committed code.
