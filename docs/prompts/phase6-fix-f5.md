# Claude Code task — Fix F5 only (self-employment entity component rounding)

Read `AGENTS.md` first. Keep `PROMPT.md` out of commits. One isolated change, one
commit. Do not touch F2/F3/F4, other engines, routers, frontend, persistence, or
extraction.

## Finding F5 (`docs/verification/findings.md`)

`corporation_dividends_2yr` recalculates to **$6,916.67** in Excel but the engine
returns **$6,916.66**. Root cause: the entity engine rounds **each component** monthly
figure to the cent before summing the entity total, while the worksheet's Summary
carries the **unrounded** component monthlies (cells `K49`/`K50` have no `ROUND`) and
rounds only the final sum (`K51`). Corporation components are 3333.33̄ + 3583.33̄ →
round-then-sum gives 6916.66; sum-then-round gives 6916.67. (Partnership is unaffected
because its components are exact at the cent; personal single-schedule kinds are
unaffected because there is no intra-entity sum.)

## Change — `app/income/self_employment_entity.py` only

Make the entity total the **round of the sum of unrounded component monthlies**,
instead of the sum of pre-rounded component monthlies. Keep each component's displayed
`qualifying_monthly` rounded to the cent (that matches the Summary cell's *display*),
but the entity-level `qualifying_monthly` must be computed from the unrounded
component values and rounded once.

Concretely, today `_component` rounds the component monthly and `_entity` sums those
rounded values. Change it so the entity sum uses the unrounded component monthly
(`qualifying_monthly(year_results)` before rounding) and rounds only the final entity
total. Implement cleanly — e.g. keep the exact component value alongside the rounded
display value, or have `_component` hand the unrounded figure to `_entity` — your call,
but no behavior change for the personal-schedule engine (`self_employment.py`) or the
shared helper (`self_employment_common.py`).

Do not change `self_employment_common.qualifying_monthly` (it already returns the
unrounded value — that's what the entity total should sum).

## Regression check

In `tests/tieout/fixtures/self_employment.json`, remove `"known_mismatch": "F5"` from
the `corporation_dividends_2yr` scenario (its `excel_expected` of `6916.67` stays). The
tie-out test then asserts it normally and should pass. The harness uses strict xfail,
so if the marker is left in place the now-passing case fails as XPASS — your reminder
that it's fixed.

Add a focused unit test (or extend an existing entity test) proving an entity total
with fractional-cent components sums **before** rounding (the corporation case is the
natural one: 3333.33̄ + 3583.33̄ → 6916.67).

## Update the finding

In `docs/verification/findings.md`, mark F5 as Resolved (with the commit), and update
the summary table: self-employment 5/5, all 18 scenarios tie out.

## Verify, then commit
```
pytest                # whole suite green; tests/tieout 18/18 pass, no xfail remaining
git add app/income/self_employment_entity.py tests/tieout/fixtures/self_employment.json \
        docs/verification/findings.md tests/unit/test_self_employment_entity.py
git commit -m "Sum unrounded self-employment entity components before rounding (F5)"
git push
```

## Out of scope
Only F5. After this, every recorded tie-out discrepancy is resolved except the
documented conventions F2/F3/F4 (which are not engine bugs).
