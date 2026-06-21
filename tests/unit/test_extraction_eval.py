import json
from uuid import uuid4

from app.schemas.extraction import BoundingBox, ExtractedField
from scripts.eval import extraction_eval


def field(name: str, value: float | None, raw_text: str | None = None) -> ExtractedField:
    return ExtractedField(
        field=name,
        value=value,
        raw_text=raw_text,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=1, y1=1, x2=2, y2=2),
    )


def test_eval_report_scores_fields_and_validation(tmp_path, monkeypatch):
    fixture_path = tmp_path / "fixtures.json"
    document_path = tmp_path / "w2.pdf"
    document_path.write_text("stub")
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "id": "bad_w2",
                    "path": str(document_path),
                    "doc_type": "w2",
                    "expected_fields": {
                        "w2_wages": 1234,
                        "w2_federal_tax_withheld": 12000,
                        "w2_employer_name": "Acme Corp",
                        "w2_employee_name": None,
                    },
                    "expect_high_review": True,
                }
            ]
        )
    )
    monkeypatch.setattr(
        extraction_eval,
        "_extract",
        lambda path, doc_type: [
            field("w2_wages", 1234),
            field("w2_federal_tax_withheld", 23500),
            field("w2_employer_name", None, "Acme Corp"),
        ],
    )

    report = extraction_eval.run_eval(extraction_eval.EvalConfig(fixtures_path=fixture_path))

    assert "| `w2_wages` | 1234 | 1234.0 | PASS |" in report
    assert "| `w2_federal_tax_withheld` | 12000 | 23500.0 | MISMATCH |" in report
    assert "| `w2_employer_name` | Acme Corp | Acme Corp | PASS |" in report
    assert "Validation high-review flag: expected True, got True (PASS)" in report


def test_eval_report_skips_missing_fixture(tmp_path):
    fixture_path = tmp_path / "fixtures.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "id": "missing",
                    "path": "test_documents/not-here.pdf",
                    "doc_type": "w2",
                    "expected_fields": {"w2_wages": 1},
                }
            ]
        )
    )

    report = extraction_eval.run_eval(extraction_eval.EvalConfig(fixtures_path=fixture_path))

    assert "SKIPPED: missing fixture" in report
