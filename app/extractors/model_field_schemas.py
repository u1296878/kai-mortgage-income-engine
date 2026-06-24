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

W2_FIELDS = {
    "tax_year": "W-2 tax year printed on the form.",
    "w2_wages": "W-2 Box 1 wages, tips, other compensation.",
    "w2_federal_tax_withheld": "W-2 Box 2 federal income tax withheld.",
    "w2_social_security_wages": "W-2 Box 3 social security wages.",
    "w2_medicare_wages": "W-2 Box 5 Medicare wages and tips.",
    "w2_employer_name": "Employer name. Return value as null and put the text in source_text.",
    "w2_employee_name": "Employee name. Return value as null and put the text in source_text.",
}

PAYSTUB_FIELDS = {
    "paystub_gross_ytd": "Pay stub year-to-date gross earnings.",
    "paystub_gross_current": "Pay stub current pay-period gross earnings.",
    "paystub_period_end": "Pay period end date. Return value as null and put the date text in source_text.",
    "paystub_pay_frequency": "Pay frequency such as weekly, bi-weekly, semi-monthly, or monthly. Return text in source_text.",
    "paystub_employer_name": "Employer name. Return value as null and put the text in source_text.",
    "paystub_employee_name": "Employee name. Return value as null and put the text in source_text.",
}

FEDERAL_FIELDS = ("tax_year", "total_income", "agi")
SCHEDULE_C_FIELDS = tuple(
    field for field in TAX_RETURN_FIELDS if field not in FEDERAL_FIELDS
)
W2_MODEL_FIELDS = tuple(W2_FIELDS)
PAYSTUB_MODEL_FIELDS = tuple(PAYSTUB_FIELDS)
LINE_NUMBER_FIELDS = {
    "total_income": ("9", ("total", "income")),
    "agi": ("11", ("adjusted", "gross", "income")),
    "schedule_c_net_profit": ("31", ("net", "profit")),
    "schedule_c_nonrecurring_income": ("6", ("other", "income")),
    "schedule_c_depletion": ("12", ("depletion",)),
    "schedule_c_depreciation": ("13", ("depreciation",)),
    "schedule_c_meals_exclusion": ("24b", ("deductible", "meals")),
    "schedule_c_business_use_of_home": ("30", ("business", "use", "home")),
    "schedule_c_business_miles": ("44", ("miles", "drove")),
}
W2_BOX_FIELDS = {
    "w2_wages": "1",
    "w2_federal_tax_withheld": "2",
    "w2_social_security_wages": "3",
    "w2_medicare_wages": "5",
}


def field_schema_for(doc_type: str) -> dict:
    return _json_schema(_fields_for_doc_type(doc_type))


def field_descriptions_for(doc_type: str) -> dict[str, str]:
    return _fields_for_doc_type(doc_type)


def schema_for_fields(field_names: tuple[str, ...]) -> dict:
    return _json_schema({name: _field_description(name) for name in field_names})


def descriptions_for_fields(field_names: tuple[str, ...]) -> dict[str, str]:
    return {name: _field_description(name) for name in field_names}


def _fields_for_doc_type(doc_type: str) -> dict[str, str]:
    if doc_type == "tax_return":
        return TAX_RETURN_FIELDS
    if doc_type == "w2":
        return W2_FIELDS
    if doc_type == "pay_stub":
        return PAYSTUB_FIELDS
    raise UnsupportedDocumentType(f"Model extraction is not configured for {doc_type}")


def _field_description(name: str) -> str:
    if name in W2_FIELDS:
        return W2_FIELDS[name]
    if name in PAYSTUB_FIELDS:
        return PAYSTUB_FIELDS[name]
    return TAX_RETURN_FIELDS[name]


def _json_schema(fields: dict[str, str]) -> dict:
    field_properties = {
        name: {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "value": {"type": ["number", "null"]},
                "confidence": {"type": ["number", "null"]},
                "source_text": {"type": ["string", "null"]},
                "text_value": {"type": ["string", "null"]},
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
