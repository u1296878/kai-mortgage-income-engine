import json
from uuid import uuid4

from app.config import settings
from app.schemas.extraction import BoundingBox, ExtractedField
from eval.extraction import harness


def field(name: str, value: float | None, raw_text: str | None = None) -> ExtractedField:
    return ExtractedField(
        field=name,
        value=value,
        raw_text=raw_text,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=1, y1=1, x2=2, y2=2),
    )


def test_eval_harness_scores_accuracy_variance_and_writes_json(tmp_path, monkeypatch):
    labels = tmp_path / "labels.json"
    document = tmp_path / "w2.pdf"
    results = tmp_path / "results"
    document.write_text("stub")
    labels.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "id": "w2",
                        "path": str(document),
                        "doc_type": "w2",
                        "expected_fields": {"w2_wages": 85000, "w2_employer_name": "Acme Corp"},
                    }
                ]
            }
        )
    )
    calls = iter(
        [
            [field("w2_wages", 85000), field("w2_employer_name", None, "Acme Corp")],
            [field("w2_wages", 84000), field("w2_employer_name", None, "Acme Corp")],
        ]
    )
    monkeypatch.setattr(harness, "_extract", lambda path, doc_type: next(calls))

    report, result = harness.run_eval(
        harness.EvalConfig(provider="anthropic", runs=2, labels_path=labels, results_dir=results)
    )

    assert "| `w2_wages` | 85000 | 85000.0, 84000.0 | 1/2 | yes |" in report
    assert result["summary"]["varied_fields"] == 1
    assert list(results.glob("anthropic-*.json"))


def test_eval_harness_reports_schedule_c_subtotal(tmp_path, monkeypatch):
    labels = tmp_path / "labels.json"
    document = tmp_path / "tax.pdf"
    document.write_text("stub")
    labels.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "id": "tax",
                        "path": str(document),
                        "doc_type": "tax_return",
                        "expected_fields": {"schedule_c_net_profit": 50000},
                        "subtotal": {"type": "schedule_c", "expected": 53000},
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(
        harness,
        "_extract",
        lambda path, doc_type: [
            field("tax_year", 2024),
            field("schedule_c_net_profit", 50000),
            field("schedule_c_depreciation", 3000),
        ],
    )

    report, result = harness.run_eval(
        harness.EvalConfig(provider="ollama", runs=1, labels_path=labels, results_dir=None)
    )

    assert "Subtotal `schedule_c`: expected 53000, got 53000.0 (PASS, 1/1)." in report
    assert result["summary"]["tieouts"] == 1


def test_eval_harness_skips_missing_documents_and_restores_settings(tmp_path):
    labels = tmp_path / "labels.json"
    labels.write_text(
        json.dumps(
            {
                "documents": [
                    {
                        "id": "missing",
                        "path": str(tmp_path / "missing.pdf"),
                        "doc_type": "w2",
                        "expected_fields": {"w2_wages": 1},
                    }
                ]
            }
        )
    )
    original_provider = settings.extraction_provider

    report, _result = harness.run_eval(
        harness.EvalConfig(provider="ollama", labels_path=labels, results_dir=None)
    )

    assert "SKIPPED: missing document" in report
    assert settings.extraction_provider == original_provider
