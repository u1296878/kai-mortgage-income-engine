from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import ResultNotFound
from app.models.result import Result
from app.repositories import result_repo
from app.schemas.extraction import ExtractedField
from app.schemas.result import CaseSummaryResponse
from app.services import income_service


def save_extraction_result(
    db: Session,
    job_id: UUID,
    document_id: UUID,
    case_id: UUID | None,
    doc_type: str,
    fields: list[ExtractedField],
) -> Result:
    annual_income, confidence, notes = income_service.compute_annual_income(
        fields,
        doc_type,
    )
    result = Result(
        job_id=str(job_id),
        document_id=str(document_id),
        case_id=str(case_id) if case_id else None,
        doc_type=doc_type,
        extracted_fields=[field.model_dump(mode="json") for field in fields],
        annual_income=annual_income,
        confidence=confidence,
        notes=notes,
    )
    saved_result = result_repo.save_result(db, result)
    log_event(
        "result_saved",
        {
            "result_id": saved_result.id,
            "document_id": saved_result.document_id,
            "annual_income": saved_result.annual_income,
        },
    )
    return saved_result


def get_case_summary(db: Session, case_id: UUID) -> CaseSummaryResponse:
    results = result_repo.list_results_by_case(db, case_id)
    total, sources = income_service.summarize_case_income(results)
    return CaseSummaryResponse(
        case_id=case_id,
        total_annual_income=total,
        results=results,
        sources=sources,
    )


def get_result(db: Session, result_id: UUID) -> Result:
    return result_repo.get_result(db, result_id)


def get_result_for_job(db: Session, job_id: UUID) -> Result:
    result = result_repo.get_result_by_job(db, job_id)
    if result is None:
        raise ResultNotFound(f"Result not found for job: {job_id}")
    return result
