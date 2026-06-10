# Claude Code task — Fix Schedule C extraction (depreciation miss + 27a over-add)

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. Scope: the Schedule C
extractor and the line-value locator heuristic, plus tests. **Do NOT change the
income engines** (`compute_schedule_c` etc.) — they tie out; the bug is extraction
feeding them wrong inputs. Keep existing `tax_return` extractor tests green.

## Context (verified on two real returns)

`compute_schedule_c` is correct. Two extraction defects make the subtotal wrong:
- **Bug A:** line 13 depreciation is never captured (label wraps across rows; the
  amount sits far right, level with the line *number*, not the matched label token).
  Understates every return.
- **Bug B:** `amortization_casualty` is mapped to line **27a (Other expenses total)**
  and added back wholesale. Per Form 1084 only the amortization/casualty portion
  itemized in Part V is added back — usually **$0**. Overstates, and fires
  inconsistently between digital and OCR.

Golden targets (synthetic fixtures, no PII — build from these numbers, do NOT commit
the real PDFs):
- 2023-style: net_profit 94,380 + depreciation 3,633 + business_use_of_home 4,628,
  other add-backs 0, 27a "other expenses" 7,557 with **no** amortization/casualty in
  Part V → subtotal **$102,641**.
- 2024-style: net_profit 85,247 + depreciation 659 + business_use_of_home 3,173,
  27a 5,046 with no amort/casualty → subtotal **$89,079**.

## Bug A — capture line 13 (and make all line values robust)

In `app/extractors/tax_return_locator.py` (the value finder used by
`schedule_c_extractor._line_money_value` → `nearest_money_value`):

- Anchor the amount search on the **line-number cell** (e.g. "13"), not the wrapped
  label text. Take the **rightmost** numeric whose `y1` is within a small band of the
  line-number row, scanning the **full page width** (the amount column is far right).
  This handles multi-row wrapped labels because the line number sits on the first row,
  level with the amount.
- Widen the row-band tolerance enough for OCR jitter (e.g. ±8–10 pt), but keep it tight
  enough not to grab the next line's amount. Keep the existing same-line then
  continuation-below fallback only as a secondary path.
- Verify this doesn't regress the existing 1040 `tax_return` line extraction (run those
  tests).

## Bug B — only add back the amortization/casualty portion of "Other expenses"

In `app/extractors/schedule_c_extractor.py`:

- **Remove** `amortization_casualty: ("27a", ("other","expenses"))` from `MONEY_LINES`
  (do not add back the 27a total).
- Read the Schedule C **Part V "Other expenses"** detail (on the Schedule C pages /
  `schedule_c_pages`) and add back **only** detail lines whose label matches
  amortization/casualty (case-insensitive: "amortization", "amortiz", "casualty").
  Sum those into `amortization_casualty`; default **0** when none match (the common
  case). If Part V can't be parsed, default 0 and set a review note rather than adding
  the total.
- Net effect: `amortization_casualty = 0` for both sample returns.

## Cross-parser consistency + tie-out tests

`tests/unit/test_schedule_c_extractor.py` (synthetic `blocks` fixtures, no PII):
- **Bug A:** a wrapped line-13 label with the amount far right, level with "13" →
  depreciation is captured (not 0). Include a case where another line's amount is just
  below, asserting we don't grab the wrong row.
- **Bug B:** a 27a "Other expenses" total with a Part V detail of only ordinary costs
  → `amortization_casualty` is 0; a Part V detail that *does* include an "Amortization"
  line → only that amount is added back.
- **Consistency:** build a digital-style block set and an OCR-style block set (slightly
  jittered y, points-scaled) for the *same* logical Schedule C and assert they extract
  identical fields.
- **Tie-out:** feed the extracted fields through `compute_schedule_c` and assert the
  subtotals equal **$102,641** and **$89,079** for the two scenarios above.

## Out of scope
No engine/worksheet changes; no rental/employment/non-taxable changes; no OCR DPI work.
The drafts remain broker-reviewable (existing behavior).

## Definition of done
- `pytest` green (new + existing). Commit (one or split A/B).
- Depreciation is captured on wrapped-label layouts; 27a is no longer added wholesale;
  digital and OCR extract the same Schedule C fields; the two scenarios tie out to the
  cent. Note in PROGRESS/TODO that Schedule C extraction defects (depreciation miss,
  27a over-add) are fixed, with a cross-parser consistency test guarding regressions.
