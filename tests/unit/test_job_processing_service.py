from uuid import uuid4

from app.exceptions import ExtractionFailed
from app.models.document import Document
from app.models.job import Job
from app.repositories import job_repo, result_repo
from app.repositories import rental_calculation_repo
from app.repositories import self_employment_calculation_repo
from app.services import extraction_service, job_processing_service
from app.schemas.extraction import BoundingBox, ExtractedField


def make_document(doc_type="other"):
    return Document(
        id=str(uuid4()),
        filename="other.pdf",
        doc_type=doc_type,
        storage_path="storage/path/other.pdf",
        broker_id=str(uuid4()),
    )


def make_pending_job(document_id):
    return Job(id=str(uuid4()), document_id=str(document_id), status="pending")


def make_field(field: str, value: float) -> ExtractedField:
    return ExtractedField(
        field=field,
        value=value,
        document_id=uuid4(),
        page=1,
        bounding_box=BoundingBox(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
    )


def test_process_next_job_returns_false_when_queue_empty(test_db):
    processed = job_processing_service.process_next_job(test_db)

    assert processed is False


def test_process_next_job_claims_and_processes_job(test_db, monkeypatch):
    document = make_document()
    job = make_pending_job(document.id)
    test_db.add_all([document, job])
    test_db.commit()
    fields = [make_field("reported_income", 18000.00)]
    monkeypatch.setattr(
        extraction_service,
        "extract_fields",
        lambda document_id, file_path, doc_type: fields,
    )

    processed = job_processing_service.process_next_job(test_db)
    result = result_repo.get_result_by_job(test_db, job.id)
    updated_job = job_repo.get_job(test_db, job.id)

    assert processed is True
    assert result is not None
    assert updated_job.status == "complete"


def test_process_next_job_marks_job_failed_on_extraction_error(test_db, monkeypatch):
    document = make_document()
    job = make_pending_job(document.id)
    test_db.add_all([document, job])
    test_db.commit()

    def raise_extraction_failed(document_id, file_path, doc_type):
        raise ExtractionFailed("extraction exploded")

    monkeypatch.setattr(extraction_service, "extract_fields", raise_extraction_failed)
    job_processing_service.process_next_job(test_db)
    updated_job = job_repo.get_job(test_db, job.id)

    assert updated_job.status == "failed"
    assert updated_job.error == "extraction exploded"


def test_process_next_job_creates_schedule_e_rental_drafts(test_db, monkeypatch):
    case_id = uuid4()
    document = make_document("tax_return")
    document.case_id = str(case_id)
    job = make_pending_job(document.id)
    test_db.add_all([document, job])
    test_db.commit()
    fields = [
        make_field("total_income", 75150.0),
        make_field("schedule_e_present", 1.0),
        make_field("schedule_e_net_rental_income", -1303.0),
        make_field("schedule_e_property_a_gross_rents", 22480.0),
        make_field("schedule_e_property_a_total_expenses", 19943.0),
        make_field("schedule_e_property_a_depreciation_depletion", 8116.0),
        make_field("tax_year", 2024.0),
        make_field("schedule_c_business_1_net_profit", 50000.0),
        make_field("schedule_c_business_1_nonrecurring_income", 5000.0),
        make_field("schedule_c_business_1_depreciation", 8000.0),
    ]
    monkeypatch.setattr(
        extraction_service,
        "extract_fields",
        lambda document_id, file_path, doc_type: fields,
    )

    processed = job_processing_service.process_next_job(test_db)
    calculations = rental_calculation_repo.list_by_case(test_db, case_id)
    self_employment = self_employment_calculation_repo.list_by_case(test_db, case_id)

    assert processed is True
    assert len(calculations) == 1
    assert len(self_employment) == 1
