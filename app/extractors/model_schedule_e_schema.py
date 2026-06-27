from app.extractors.model_prompt import page_text

FIELD_NAMES = (
    "address",
    "fair_rental_days",
    "rents_received",
    "insurance",
    "mortgage_interest",
    "other_interest",
    "taxes",
    "depreciation_depletion",
    "total_expenses",
)


def schedule_e_prompt(blocks: list[dict]) -> str:
    return (
        "Extract Schedule E rental properties from the attached tax-return images. "
        "Return a properties array, one item per property column A, B, or C. "
        "Do not extract PITIA or property type; those are underwriter inputs. "
        "For blank numeric line items, return 0, not the printed line number. "
        "Each field object should include value, confidence, source_text, box, "
        "and page_index. Use normalized 0.0-1.0 image coordinates for box, or "
        "null when not placeable. Fields: address line 1a, fair_rental_days line 2, "
        "rents_received line 3, insurance line 9, mortgage_interest line 12, "
        "other_interest line 13, taxes line 16, depreciation_depletion line 18, "
        f"total_expenses line 20.\n\nOCR text:\n{page_text(blocks)}"
    )


def schedule_e_schema() -> dict:
    field_schema = {
        "type": ["object", "null"],
        "additionalProperties": False,
        "properties": {
            "value": {"type": ["number", "string", "null"]},
            "confidence": {"type": ["number", "null"]},
            "source_text": {"type": ["string", "null"]},
            "text_value": {"type": ["string", "null"]},
            "box": {
                "type": ["array", "null"],
                "items": {"type": "number"},
                "minItems": 4,
                "maxItems": 4,
            },
            "page_index": {"type": ["integer", "null"]},
        },
        "required": ["value", "confidence", "source_text", "box", "page_index"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "properties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"column": {"type": "string"}, **{name: field_schema for name in FIELD_NAMES}},
                    "required": ["column", *FIELD_NAMES],
                },
            }
        },
        "required": ["properties"],
    }
