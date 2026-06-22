from uuid import uuid4

from app.schemas.extraction import BoundingBox, ExtractedField
from app.services import extraction_validation


def field(name: str, value: float | None, confidence: float = 1.0) -> ExtractedField:
    return ExtractedField(
        field=name,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
        confidence=confidence,
    )


def test_w2_withholding_greater_than_wages_is_high_flag():
    issues = extraction_validation.validate_extraction(
        "w2",
        [
            field("w2_wages", 1234.0),
            field("w2_federal_tax_withheld", 23500.0),
        ],
    )

    assert _messages(issues) == ["W-2 Box 2 federal withholding exceeds Box 1 wages."]
    assert issues[0]["severity"] == "high"


def test_clean_w2_has_no_high_flags():
    issues = extraction_validation.validate_extraction(
        "w2",
        [
            field("w2_wages", 85000.0),
            field("w2_federal_tax_withheld", 12000.0),
        ],
    )

    assert not extraction_validation.has_high_issue(issues)


def test_tax_return_agi_greater_than_total_income_is_high_flag():
    issues = extraction_validation.validate_extraction(
        "tax_return",
        [field("total_income", 80000.0), field("agi", 90000.0)],
    )

    assert _messages(issues) == ["AGI exceeds total income."]
    assert issues[0]["severity"] == "high"


def test_schedule_c_net_profit_mismatch_is_high_flag():
    issues = extraction_validation.validate_extraction(
        "tax_return",
        [
            field("schedule_c_net_profit", 94380.0),
            field("schedule_c_business_1_net_profit", 90000.0),
        ],
    )

    assert "Schedule C net profit readings disagree." in _messages(issues)


def test_schedule_c_matching_net_profit_has_no_mismatch_flag():
    issues = extraction_validation.validate_extraction(
        "tax_return",
        [
            field("schedule_c_net_profit", 94380.0),
            field("schedule_c_business_1_net_profit", 94380.5),
        ],
    )

    assert "Schedule C net profit readings disagree." not in _messages(issues)


def test_scanned_style_missing_addback_is_low_flag():
    issues = extraction_validation.validate_extraction(
        "tax_return",
        [
            field("schedule_c_net_profit", 85247.0),
            field("schedule_c_depreciation", None),
            field("schedule_c_business_use_of_home", 3173.0),
        ],
    )

    assert issues == [
        {
            "fields": ["schedule_c_depreciation"],
            "message": "schedule_c_depreciation may be a missing Schedule C add-back; verify against the form.",
            "severity": "low",
        }
    ]


def test_indexed_schedule_c_missing_addback_is_low_flag():
    issues = extraction_validation.validate_extraction(
        "tax_return",
        [
            field("schedule_c_business_1_net_profit", 85247.0),
            field("schedule_c_business_1_depreciation", None),
            field("schedule_c_business_1_business_use_of_home", 3173.0),
        ],
    )

    assert issues == [
        {
            "fields": ["schedule_c_business_1_depreciation"],
            "message": "schedule_c_business_1_depreciation may be a missing Schedule C add-back; verify against the form.",
            "severity": "low",
        }
    ]


def test_clean_2023_style_return_has_no_flags():
    issues = extraction_validation.validate_extraction(
        "tax_return",
        [
            field("total_income", 94380.0),
            field("agi", 87638.0),
            field("schedule_c_net_profit", 94380.0),
            field("schedule_c_depreciation", 3633.0),
            field("schedule_c_business_use_of_home", 4628.0),
        ],
    )

    assert issues == []


def test_field_level_reconciliation_issue_reaches_validation_flags():
    issue = {
        "fields": ["schedule_c_net_profit"],
        "message": "schedule_c_net_profit: model read 1 but Form line 31 shows 85,247; used the form value; verify.",
        "severity": "high",
    }
    flagged = field("schedule_c_net_profit", 85247.0)
    flagged.review_flags.append(issue)

    issues = extraction_validation.validate_extraction("tax_return", [flagged])

    assert issue in issues
    assert extraction_validation.has_high_issue(issues)


def _messages(issues):
    return [issue["message"] for issue in issues]
