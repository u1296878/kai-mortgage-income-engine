"""Tie-out tests: engine output must equal the real Excel worksheet to the cent.

excel_expected values are produced by scripts/tieout/excel_oracle.py (LibreOffice
recalculation of the company's actual worksheets) and stored in fixtures/*.json.
This suite asserts the engine matches. Scenarios marked `known_mismatch` are recorded
discrepancies (see docs/verification/findings.md); they are strict-xfail, so the build
stays green while the gap is documented, and it flips to a failure (XPASS) the moment
the engine is changed to match — a built-in reminder to update the finding.
"""

import json
from pathlib import Path

import pytest

from tests.tieout.builders import compute_engine

FIXTURES = Path(__file__).parent / "fixtures"


def _params():
    params = []
    for path in sorted(FIXTURES.glob("*.json")):
        worksheet = path.stem
        data = json.loads(path.read_text())
        for scn in data["scenarios"]:
            marks = []
            if scn.get("known_mismatch"):
                marks = [pytest.mark.xfail(
                    reason=f"recorded mismatch {scn['known_mismatch']} (docs/verification/findings.md)",
                    strict=True,
                )]
            params.append(pytest.param(worksheet, scn, id=f"{worksheet}::{scn['id']}", marks=marks))
    return params


@pytest.mark.parametrize("worksheet,scenario", _params())
def test_engine_ties_out_to_excel(worksheet, scenario):
    engine_value = compute_engine(worksheet, scenario["engine_input"])

    assert round(engine_value, 2) == round(scenario["excel_expected"], 2)
