# Claude Code task — Revert the locator regression, gate it, fix Schedule C by column

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. Three ordered commits. Do NOT
change income engines. **Do NOT modify the shared `tax_return_locator.py` heuristic
again** to chase Schedule C fields — that is what regressed the 1040 fields last time.

## Background

Commit `3427840` widened the shared `tax_return_locator.py` and regressed multiple
1040/Schedule C fields: business_use_of_home now grabs "Form **8829**" (a form
reference), line 6 grabs gross receipts ($145,721), total_income grabs a Schedule 1
figure, and depreciation grabs line 23 Taxes. The only good part was the Schedule C
**Bug B** change (27a no longer added wholesale; Part V token approach) — keep that.

## Commit 1 — Revert the locator regression (restore baseline; keep Bug B)

- Restore `app/extractors/tax_return_locator.py` to its `0d57aa9` state (i.e. revert
  only the `3427840` changes to that file).
- Keep the Schedule C Bug B changes in `schedule_c_extractor.py` and the new
  `tax_return_text.py` helper. Ensure imports still resolve after the locator revert.
- Run the existing `tax_return` tests and confirm the 1040 fields are correct again:
  business_use_of_home = 4,628 / 3,173, nonrecurring_income (line 6) = 0,
  total_income = 94,380 (2023). Depreciation will be back to "missed (0)" — that's
  expected; Commit 3 fixes it. The point of Commit 1 is to remove the catastrophic
  negative 2023 result immediately.

## Commit 2 — Adversarial golden fixtures (the gate)

`tests/unit/test_schedule_c_extractor.py` (synthetic `blocks`, **no PII** — build from
the numbers below; do not commit the real PDFs). Replicate the real layout *traps*:

- A wrapped **line 13** label across rows, with the depreciation amount in the right
  amount column level with the "13" number, and a **line 23 "Taxes and licenses"**
  amount ($10,959) nearby — assert depreciation = 3,633, NOT 10,959.
- A **"Form 8829"** reference on/near the line 30 row — assert business_use_of_home =
  4,628, NOT 8,829.
- **Gross receipts** ($145,721) near line 1/line 6 — assert nonrecurring_income
  (line 6) = 0, NOT 145,721.
- 27a "Other expenses" total with a Part V detail of only ordinary costs → amort = 0;
  and a second case where Part V *does* list "Amortization" → only that is added.
- Provide BOTH a digital-style block set and an **OCR-style** set (y-jitter,
  points-scaled) for the same logical Schedule C, and assert identical fields.
- A tie-out test feeding extracted fields → `compute_schedule_c`: subtotals must equal
  **$102,641** (2023: net 94,380 + depr 3,633 + BUOH 4,628) and **$89,079**
  (2024: net 85,247 + depr 659 + BUOH 3,173).

These tests should FAIL after Commit 1 (depreciation missed) and PASS after Commit 3.

## Commit 3 — Column-aware Schedule C reader (contained, no shared-locator changes)

Add a Schedule-C-specific value finder in `schedule_c_extractor.py` (do not touch the
shared locator). Approach:

- **Anchor on the left-margin line-number token** (a block whose text is exactly the
  line number, e.g. "13"/"30"/"6", in the form's left x-region) on the Schedule C page.
- **Read the amount column:** take the rightmost numeric block whose `y1` is within a
  tight band of that line-number row (±~6 pt; widen modestly for OCR) AND whose `x`
  falls in the **right-hand amount-column band**. Derive the amount-column x-range from
  a known-good line (e.g. net profit line 31) so it scales for digital and OCR rather
  than hardcoding.
- **Guards:** ignore a number that is a form reference — preceded by "Form"/"see" on
  the row, or a bare 4-digit IRS form number (8829, 4562, 6198, 8995, 1040) outside the
  amount column. The amount-column x-range guard alone should exclude "Form 8829" and
  gross-receipts numbers that sit in the label region.
- Must pass every Commit-2 fixture (digital + OCR) and not regress the 1040 tests.

## Stop rule (honest gate)
If the column-aware reader cannot pass the adversarial digital+OCR fixtures without
breaking another field, do not keep widening it — stop and report which fields conflict.
That's the signal this document class needs AI-assisted extraction; do not start that
here.

## Out of scope
Income engines, rental/employment/non-taxable, the shared 1040 locator heuristic
(beyond the Commit-1 revert), OCR DPI.

## Definition of done
- Commit 1: 1040 fields correct again, no catastrophic 2023; tests green.
- Commit 2: adversarial fixtures committed (failing on depreciation).
- Commit 3: depreciation captured (3,633 / 659), 27a not over-added, digital == OCR,
  subtotals tie out to $102,641 / $89,079, 1040 tests still green. Note in
  PROGRESS/TODO that Schedule C extraction is column-aware and gated by adversarial
  digital+OCR fixtures.
