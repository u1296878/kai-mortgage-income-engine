# Tie-out verification

Proves the calc engines match the company's **actual Excel worksheets** to the cent.

## Layout
- `fixtures/*.json` — scenarios with `engine_input` + `excel_expected` (the oracle).
- `builders.py` — read-only bridge from a fixture's `engine_input` to an engine call.
- `test_tieout.py` — asserts each engine value equals `excel_expected`; recorded
  mismatches (`known_mismatch`) are strict-xfail.
- generator: `scripts/tieout/excel_oracle.py`.

## Run the assertions (CI / anywhere with the app deps)
```
pytest tests/tieout
```
No Excel or LibreOffice needed — the JSON fixtures are the committed oracle.

## Regenerate `excel_expected` (only when worksheets or scenarios change)
Needs LibreOffice (`soffice`) + openpyxl and the real, **uncommitted** workbooks:
```
python scripts/tieout/excel_oracle.py --workbooks-dir /path/to/worksheets
```
This recalculates the worksheets and rewrites `excel_expected` in place. The source
`.xlsx` files are intentionally not committed.

## Findings
Discrepancies are tracked in `docs/verification/findings.md` (F1–F4). The harness
does not "fix" mismatches — it records them and xfails the affected scenario.
