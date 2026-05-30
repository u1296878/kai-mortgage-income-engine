from uuid import uuid4

from app.models.result import Result


def seed_result(test_db, case_id, doc_type, fields, income_stream_id=None):
    document_id = uuid4()
    extracted_fields = [
        {
            "field": field["field"],
            "value": field["value"],
            "document_id": str(document_id),
            "page": 1,
            "bounding_box": {"x1": 1, "y1": 1, "x2": 2, "y2": 2},
            "raw_text": field.get("raw_text"),
        }
        for field in fields
    ]
    annual_income = next((field["value"] for field in fields if field["value"] > 0), 50000.0)
    result = Result(
        id=str(uuid4()),
        job_id=str(uuid4()),
        document_id=str(document_id),
        case_id=str(case_id),
        income_stream_id=income_stream_id,
        doc_type=doc_type,
        extracted_fields=extracted_fields,
        annual_income=annual_income,
        confidence="medium",
    )
    test_db.add(result)
    test_db.commit()
    return result


def w2_fields(employer_name):
    return [
        {"field": "w2_wages", "value": 85000.0, "raw_text": None},
        {"field": "w2_employer_name", "value": 0.0, "raw_text": employer_name},
        {"field": "w2_tax_year", "value": 2023.0, "raw_text": None},
    ]


def rental_fields(address):
    return [
        {"field": "rental_net_income", "value": 18000.0, "raw_text": None},
        {"field": "property_address", "value": 0.0, "raw_text": address},
        {"field": "tax_year", "value": 2023.0, "raw_text": None},
    ]
