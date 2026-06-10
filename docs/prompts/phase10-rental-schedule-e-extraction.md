# Claude Code task — Per-property Schedule E rental extraction → rental engine

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. Larger feature; commit in
the parts below. Do NOT change the employment/non-taxable/self-employment engines or
the manual rental worksheet UI behavior. The validated rental engine
(`app/income/rental.py`) is the calc authority — reuse it, don't reimplement.

## Problem (confirmed on two real tax returns)

The document rental path (`app/extractors/rental_extractor.py`) reads only gross
(line 3), total expenses (line 20), and **net (line 26)** — it has NO Schedule E
add-backs (depreciation L18, mortgage interest L12+L13, taxes L16, insurance L9), so
it reports net rental income and understates qualifying income ~8–11× (e.g. a return
that should qualify ~$2,700/mo reports ~$287/mo). It also can't handle the 3 property
columns (A/B/C) or exclude a non-borrowing spouse's property.

Fix: extract **per-property** Schedule E line items and feed each into the rental
engine (with add-backs and months-in-service), and let the broker include/exclude
each property.

## Part A — Per-property Schedule E parser

New `app/extractors/schedule_e_extractor.py` (keep `rental_extractor.py` for now or
delegate to this). For each rental property column (A/B/C) on the Schedule E page,
extract: physical address, fair-rental days (line 2), rents received (L3),
insurance (L9), mortgage interest (L12), other interest (L13), taxes (L16),
depreciation/depletion (L18), total expenses (L20).

Key parsing requirements (these forms are messy — verify against real output):
- **Assign amounts to columns A/B/C by x-position.** The three columns sit in
  distinct x-bands (observed ~x360 / ~x460 / ~x560). Derive the band boundaries from
  the "Income: A B C" header row (or the line value positions) rather than hardcoding.
- Handle pdfplumber's **dotted-leader fragmentation** — `extract_words` splits/garbles
  numbers on these IRS forms. Use tuned extraction (e.g. table/line-aware settings or
  post-filtering of leader artifacts) and validate that per-column sums match the
  Schedule E total lines (L23a rents, L23e total expenses, L23c mortgage interest,
  L23d depreciation) as a built-in correctness check.
- `months_in_service = min(fair_rental_days / 30, 12)`, default 12 if days missing.

## Part B — Map each property into the rental engine

For each extracted property build a `RentalProperty` (spec section 4 / `rental.py`):
- `schedule_e_years = [one ScheduleEYear]` with `rents_received`, `total_expenses`,
  `insurance`, `mortgage_interest = L12 + L13`, `taxes`, `depreciation_depletion = L18`,
  `months_in_service`. (HOA/casualty not on Sch E → 0.)
- `property_class` and `monthly_pitia` are NOT on the return — leave them as broker
  inputs (default to the gross Schedule-E add-back figure; the broker sets investment
  + PITIA in review).
- Run `compute_rental_income` to get each property's qualifying monthly **with the
  add-backs**. This replaces the line-26-net logic for documents.

Sanity targets (2024 return, verify to the cent once column assignment is right):
property A ≈ $1,483.75/mo (12 mo), property B ≈ $1,265.13/mo (240 days → 8 mo).

## Part C — Broker review: per-property include/exclude

Surface each extracted property as a **pre-filled rental calculation draft** on the
case (reuse the existing `rental_calculation` model/endpoints/UI), so the broker can:
edit, set property_class + PITIA, and **include or exclude** each property (needed to
drop a non-borrowing spouse's property or a short-term-rental that doesn't qualify).
Only included properties feed the case summary. Do not auto-trust extraction as final
— extraction pre-fills, the broker confirms.

## Part D — Tests

- **Do NOT commit the real tax-return PDFs — they contain real SSNs and names.**
  Build synthetic Schedule E `blocks` fixtures (the parser's input shape) that mirror
  the structure: 2–3 property columns, dotted leaders, the line items above. Include a
  multi-property case and a single-property case.
- Unit-test the parser (correct per-column assignment; per-column sums equal the L23
  totals) and the engine mapping (per-property qualifying with add-backs and
  months-in-service). Cover a property with <12 fair-rental months and a loss property.
- Behavioral tests for include/exclude affecting the case rental total.

## Out of scope
- No change to other income engines or the manual worksheet calc. No ownership
  auto-detection (broker decides inclusion). No OCR-path changes beyond feeding the
  same block format.

## Definition of done
- `pytest` green; `npm run test`/`build` pass. Commit per part.
- A tax return with multiple Schedule E properties produces per-property qualifying
  income **with add-backs and months-in-service**, the broker can include/exclude each,
  and the case summary reflects only included properties — numbers in line with the
  worksheet engine, not the old line-26 net. Note in PROGRESS/TODO that rental document
  extraction now uses the validated engine; the old net-only path is retired.
