# Claude Code task — Fix the PDF source-highlight position (wrong y-axis)

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. This is a UI/coordinate fix
only — do NOT change any calc engine, extraction values, routers, persistence, or the
worker. The bounding-box numbers in results are correct; only the overlay placement
(and OCR coordinate units) are wrong.

## Bug

Clicking "View in PDF" highlights the wrong vertical spot — far too high. Example:
`total_income` on a 1040 has `bounding_box y1≈619, y2≈631` (line 9, ~78% down an
~792-pt page), but the highlight renders near the top (~20% down).

Root cause — `frontend/src/components/DocumentViewer.tsx`, `buildHighlight`:
```js
top: (metrics.heightPoints - source.bounding_box.y2) * metrics.scale + 8,
```
This flips the y-axis as if the box were in PDF-native **bottom-left** coordinates.
But the parser stores **top-left** coordinates (`app/parsers/pdf_parser.py` maps
`y1 = word["top"]`, `y2 = word["bottom"]` — pdfplumber measures from the top), which
matches AGENTS.md ("x1/y1 is top-left … in PDF points"). So the flip is wrong.

## Fix 1 — DocumentViewer (the reported bug)

In `buildHighlight`, use `y1` directly with no flip:
```js
top: source.bounding_box.y1 * metrics.scale + 8,
```
`height` stays `(y2 - y1) * metrics.scale`. After this, `PageMetrics.heightPoints`
is unused — remove it from the type and from `setMetrics` (no dead code), keeping
`scale`.

Update `frontend/src/components/DocumentViewer.test.tsx` so it asserts the overlay
`top` reflects `y1` (top-left origin) rather than the old flipped value. Add/keep a
case with a known box (e.g. y1=619, y2=631 on a 792-pt page) asserting top ≈
y1*scale, not (height−y2)*scale.

## Fix 2 — OCR coordinate units (related latent bug for scanned docs)

`app/parsers/ocr_parser.py` stores Tesseract `left/top/width/height` in **pixels at
150 DPI**, but the viewer (and AGENTS.md) expect **PDF points**. Scanned docs would
be mis-scaled ~2× even after Fix 1.

- Define a `DPI = 150` constant; use it in `_convert_single_page` (`dpi=DPI`) and to
  scale in `_ocr_data_to_blocks`: multiply `left/top/width/height` by `72 / DPI` so
  the stored block is in top-left PDF points, consistent with `pdf_parser`.
- Update the OCR parser's tests to expect point-scaled coordinates.

This keeps both parsers on one convention (top-left, PDF points) so the single viewer
transform works for digital and scanned documents alike.

## Out of scope
- No change to extraction field values, income engines, the income worksheets, the
  worker, routers, or persistence. Only the viewer transform, the OCR coordinate
  units, and their tests.

## Definition of done
- Frontend: `npm run test` + `npm run build` pass; the highlight lands on the correct
  line (verify with the 1040 `total_income` case — it should sit on line 9, right-hand
  amount column). Backend: `pytest` green with the updated OCR-parser test.
- Commit+push (one commit is fine, or split frontend/backend). Note in PROGRESS/TODO
  that source-highlight coordinates are now uniformly top-left PDF points.
