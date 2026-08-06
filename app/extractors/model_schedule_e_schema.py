from app.extractors.model_prompt import source_line_text
from app.extractors.source_lines import SourceLine

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


def schedule_e_prompt(blocks: list[dict], source_lines: list[SourceLine] | None = None) -> str:
    return (
        "Extract Schedule E rental properties from the attached tax-return images. "
        "Return strict JSON matching the supplied schema with a properties array, "
        "one item per property column A, B, or C. "
        "Do not extract PITIA or property type; those are underwriter inputs. "
        "Each field object should include value, confidence, source_text, and "
        "source_line_ids. Use source_line_ids from bracketed IDs only, such as "
        "L0007. Do not invent source IDs or return coordinates. If a field is "
        "not visible, return value null, source_text null, and source_line_ids []. "
        "Never compute income or infer missing values. Fields: address line 1a, "
        "fair_rental_days line 2, "
        "rents_received line 3, insurance line 9, mortgage_interest line 12, "
        "other_interest line 13, taxes line 16, depreciation_depletion line 18, "
        f"total_expenses line 20.\n\nSource lines:\n{source_line_text(blocks, source_lines)}"
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
            "source_line_ids": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["value", "confidence", "source_text", "source_line_ids"],
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
