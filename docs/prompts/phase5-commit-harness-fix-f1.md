# Claude Code task — Commit the tie-out harness, then fix F1 only

Two ordered steps. Do them as two separate commits. Read `AGENTS.md` first; keep
`PROMPT.md` out of commits.

## Step 1 — Commit the verification harness (no code behavior change)

These files already exist in the working tree (written during verification). Stage
ONLY them — do not stage `PROMPT.md`, and do not `git add -A`:

```
git add scripts/tieout tests/tieout docs/verification
git status            # confirm: only scripts/tieout, tests/tieout, docs/verification staged
git commit -m "Add Excel-oracle tie-out harness and verification fixtures"
git push
```

Sanity-check before committing: `pytest tests/tieout` should be green, with
`employment::partial_month_fractional` showing as **xfail** (it's a recorded mismatch
— finding F1). If the engine deps resolve and that's the state, commit.

## Step 2 — Fix F1 only (employment partial-month rounding)

**Finding F1 (`docs/verification/findings.md`):** Excel's "# of months" column is
`ROUND(months, 2)` and the qualifying blend divides by the sum of the *rounded*
months. The engine uses full-precision `months_between`, so fractional-month periods
drift (e.g. 15/31 → Excel 0.48 vs engine 0.483871; $5,008.01 vs $5,006.46).

**Change — `app/income/employment.py` only.** Round each period's month count to 2 dp
before it is used, matching the worksheet:

- In `_period_results`, where it computes `months = months_between(period.date_from, period.date_through)`,
  wrap it: `months = round(months_between(period.date_from, period.date_through), 2)`.
- In `_blend`, the non-annualized branch `months = months_between(period.date_from, period.date_through)`
  becomes `months = round(months_between(period.date_from, period.date_through), 2)`.
  Leave the annualize branch (`months = 12.0`) unchanged.

Do **not** change `app/income/dates.py` (`months_between` stays full-precision — only
employment rounds it, mirroring the `I = ROUND(J,2)` column). Do not touch any other
engine, router, frontend, persistence, or extraction code.

**Flip the regression marker:** in `tests/tieout/fixtures/employment.json`, remove the
`"known_mismatch": "F1"` key from the `partial_month_fractional` scenario (its
`excel_expected` of `5008.01` stays). The tie-out test will now assert it normally —
it should pass. (The harness uses strict xfail, so if you forget to remove the marker
the now-passing case fails as XPASS — a built-in reminder.)

**Update the finding:** in `docs/verification/findings.md`, mark F1 as Resolved with
the commit that fixed it.

**Verify, then commit:**
```
pytest                # whole suite green; tests/tieout employment all pass (no xfail)
git add app/income/employment.py tests/tieout/fixtures/employment.json docs/verification/findings.md
git commit -m "Round employment per-period months to 2dp to tie out to worksheet (F1)"
git push
```

## Out of scope
Only F1. Do not fix F2/F3/F4 (they are convention/usability notes, not engine bugs).
No other files. Confirm the 17 previously-passing tie-out scenarios still pass and
`partial_month_fractional` now passes too (18/18).
