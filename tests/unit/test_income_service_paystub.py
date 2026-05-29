from uuid import uuid4

from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import income_service


def make_field(field: str, value: float, raw_text: str | None = None) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
        raw_text=raw_text,
    )


def test_annualize_ytd_uses_current_month(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return type("Now", (), {"month": 5})()

    monkeypatch.setattr(income_service, "datetime", FakeDateTime)
    fields = [make_field("gross_ytd", 42500.0)]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "pay_stub")

    assert annual_income == 102000.0


def test_annualize_period_biweekly():
    fields = [
        make_field("gross_this_period", 3269.23),
        make_field("pay_period_type", 0.0, "biweekly"),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "pay_stub")

    assert annual_income == 84999.98


def test_confidence_medium_when_ytd_and_period_differ_over_20pct(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return type("Now", (), {"month": 5})()

    monkeypatch.setattr(income_service, "datetime", FakeDateTime)
    fields = [
        make_field("gross_ytd", 42500.0),
        make_field("gross_this_period", 1000.0),
        make_field("pay_period_type", 0.0, "biweekly"),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "pay_stub")

    assert confidence == "medium"
    assert "differ by" in notes


def test_confidence_high_when_ytd_and_period_agree_within_20pct(monkeypatch):
    class FakeDateTime:
        @classmethod
        def now(cls):
            return type("Now", (), {"month": 5})()

    monkeypatch.setattr(income_service, "datetime", FakeDateTime)
    fields = [
        make_field("gross_ytd", 42500.0),
        make_field("gross_this_period", 3269.23),
        make_field("pay_period_type", 0.0, "biweekly"),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "pay_stub")

    assert confidence == "high"
    assert notes is None


def test_confidence_low_when_only_period_available():
    fields = [
        make_field("gross_this_period", 3269.23),
        make_field("pay_period_type", 0.0, "biweekly"),
    ]

    annual_income, confidence, notes = income_service.compute_annual_income(fields, "pay_stub")

    assert confidence == "low"
