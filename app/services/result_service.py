from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.exceptions import CaseNotFound, DocumentNotFound, JobNotFound, ResultNotFound
from app.models.result import Result
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories import (
    borrower_repo,
    case_repo,
    document_repo,
    employment_calculation_repo,
    income_stream_repo,
    job_repo,
    rental_calculation_repo,
    result_repo,
)
from app.schemas.extraction import ExtractedField
from app.schemas.result import CaseSummaryResponse
from app.services import case_summary_builder, income_service


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


def get_case_summary(
    db: Session,
    case_id: UUID,
    current_user: User,
) -> CaseSummaryResponse:
    case = case_repo.get_case(db, case_id)
    if not _is_manager(current_user) and case.broker_id != current_user.id:
        raise CaseNotFound(f"Case not found: {case_id}")
    results = result_repo.list_results_by_case(db, case_id)
    borrowers = borrower_repo.list_borrowers_by_case(db, case_id)
    income_streams = income_stream_repo.list_income_streams_by_case(db, case_id)
    employment_calculations = employment_calculation_repo.list_by_case(db, case_id)
    rental_calculations = rental_calculation_repo.list_by_case(db, case_id)
    return case_summary_builder.build_case_summary(
        case_id=case_id,
        borrowers=borrowers,
        income_streams=income_streams,
        results=results,
        employment_calculations=employment_calculations,
        rental_calculations=rental_calculations,
    )


def get_result(db: Session, result_id: UUID, current_user: User) -> Result:
    result = result_repo.get_result(db, result_id)
    _ensure_result_access(db, result, current_user)
    return result


def get_result_for_job(db: Session, job_id: UUID, current_user: User) -> Result:
    try:
        job = job_repo.get_job(db, job_id)
    except JobNotFound as error:
        raise ResultNotFound(f"Result not found for job: {job_id}") from error
    _ensure_job_access(db, job, current_user)
    result = result_repo.get_result_by_job(db, job_id)
    if result is None:
        raise ResultNotFound(f"Result not found for job: {job_id}")
    return result


def _ensure_result_access(db: Session, result: Result, current_user: User) -> None:
    if _is_manager(current_user):
        return
    try:
        document = document_repo.get_document(db, UUID(result.document_id))
    except DocumentNotFound as error:
        raise ResultNotFound(f"Result not found: {result.id}") from error
    if document.broker_id != current_user.id:
        raise ResultNotFound(f"Result not found: {result.id}")


def _ensure_job_access(db: Session, job, current_user: User) -> None:
    if _is_manager(current_user):
        return
    try:
        document = document_repo.get_document(db, UUID(job.document_id))
    except DocumentNotFound as error:
        raise ResultNotFound(f"Result not found for job: {job.id}") from error
    if document.broker_id != current_user.id:
        raise ResultNotFound(f"Result not found for job: {job.id}")


def _is_manager(user: User) -> bool:
    return user.role == UserRole.manager.value
