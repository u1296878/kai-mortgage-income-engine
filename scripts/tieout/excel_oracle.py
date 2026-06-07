"""Excel-oracle fixture generator for income-engine tie-out.

Fills scenario inputs into the real company worksheets, recalculates them with
LibreOffice headless, reads the qualifying output cell, and writes the
`excel_expected` value into the JSON fixtures the pytest harness asserts against.

Usage:
    python scripts/tieout/excel_oracle.py --workbooks-dir /path/to/worksheets
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import openpyxl
from excel_adapters import ADAPTERS


def main() -> None:
    args = _parse_args()
    workbook_dir = Path(args.workbooks_dir)
    fixture_dir = Path(args.out)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for worksheet in args.worksheets:
            _refresh_fixture(worksheet, workbook_dir, fixture_dir, temp_path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbooks-dir", required=True)
    parser.add_argument("--out", default="tests/tieout/fixtures")
    parser.add_argument("--worksheets", nargs="*", default=list(ADAPTERS))
    return parser.parse_args()


def _refresh_fixture(
    worksheet: str,
    workbook_dir: Path,
    fixture_dir: Path,
    temp_path: Path,
) -> None:
    adapter = ADAPTERS[worksheet]
    fixture_path = fixture_dir / f"{worksheet}.json"
    data = json.loads(fixture_path.read_text())
    workbook = workbook_dir / adapter["workbook"]
    for scenario in data["scenarios"]:
        scenario["excel_expected"] = _excel_value(
            workbook,
            adapter["apply"],
            scenario["engine_input"],
            temp_path,
        )
    fixture_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"{worksheet}: refreshed {len(data['scenarios'])} scenarios")


def _excel_value(workbook: Path, apply_adapter, engine_input: dict, temp_path: Path):
    work_path = temp_path / f"work_{os.urandom(4).hex()}.xlsx"
    shutil.copy(workbook, work_path)
    os.chmod(work_path, 0o644)
    workbook_obj = openpyxl.load_workbook(work_path)
    sheet, cell = apply_adapter(workbook_obj, engine_input)
    workbook_obj.save(work_path)
    recalculated = openpyxl.load_workbook(
        _recalc(work_path, temp_path / "recalc"),
        data_only=True,
    )
    value = recalculated[sheet][cell].value
    return round(float(value), 2) if isinstance(value, (int, float)) else None


def _recalc(xlsx_path: Path, outdir: Path) -> Path:
    subprocess.run(
        [
            "soffice",
            "--headless",
            "--calc",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(outdir),
            str(xlsx_path),
        ],
        check=True,
        capture_output=True,
    )
    return outdir / xlsx_path.name


if __name__ == "__main__":
    main()
