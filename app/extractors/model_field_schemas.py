from app.exceptions import UnsupportedDocumentType


TAX_RETURN_FIELDS = {
    "tax_year": "Form 1040 tax year.",
    "total_income": "Form 1040 total income.",
    "agi": "Form 1040 adjusted gross income.",
    "schedule_c_net_profit": "Schedule C line 31 net profit or loss.",
    "schedule_c_nonrecurring_income": "Schedule C line 6 other income.",
    "schedule_c_depletion": "Schedule C line 12 depletion.",
    "schedule_c_depreciation": "Schedule C line 13 depreciation and section 179.",
    "schedule_c_meals_exclusion": "Schedule C line 24b deductible meals.",
    "schedule_c_business_use_of_home": "Schedule C line 30 business use of home.",
    "schedule_c_business_miles": "Schedule C line 44a business miles.",
    "schedule_c_amortization_casualty": (
        "Schedule C Part V amortization or casualty-loss amount only."
    ),
}


def field_schema_for(doc_type: str) -> dict:
    if doc_type != "tax_return":
        raise UnsupportedDocumentType(f"Model extraction is not configured for {doc_type}")
    return _json_schema(TAX_RETURN_FIELDS)


def field_descriptions_for(doc_type: str) -> dict[str, str]:
    if doc_type != "tax_return":
        raise UnsupportedDocumentType(f"Model extraction is not configured for {doc_type}")
    return TAX_RETURN_FIELDS


def _json_schema(fields: dict[str, str]) -> dict:
    field_properties = {
        name: {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "value": {"type": ["number", "null"]},
                "confidence": {"type": ["number", "null"]},
                "source_text": {"type": ["string", "null"]},
            },
            "required": ["value", "confidence", "source_text"],
        }
        for name in fields
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "fields": {
                "type": "object",
                "additionalProperties": False,
                "properties": field_properties,
                "required": list(fields),
            }
        },
        "required": ["fields"],
    }
