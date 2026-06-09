from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.audit.logger import log_event
from app.models.job_status import JobStatus
from app.repositories import document_repo, job_repo
from app.services import (
    extraction_service,
    result_service,
    schedule_c_se_service,
    schedule_e_rental_service,
)


def process_next_job(db: Session) -> bool:
    job = None
    try:
        job = job_repo.claim_next_pending_job(db)
        if job is None:
            return False
        document = document_repo.get_document(db, UUID(job.document_id))
        fields = extraction_service.extract_fields(
            UUID(document.id),
            Path(document.storage_path),
            document.doc_type,
        )
        result = result_service.save_extraction_result(
            db,
            UUID(job.id),
            UUID(document.id),
            UUID(document.case_id) if document.case_id else None,
            document.doc_type,
            fields,
        )
        if document.doc_type == "tax_return" and document.case_id and document.broker_id:
            schedule_e_rental_service.create_drafts_from_fields(
                db,
                UUID(document.case_id),
                UUID(document.broker_id),
                UUID(document.id),
                fields,
            )
            schedule_c_se_service.create_drafts_from_fields(
                db,
                UUID(document.case_id),
                UUID(document.broker_id),
                UUID(document.id),
                fields,
            )
        job_repo.update_job_status(db, UUID(job.id), JobStatus.complete.value)
        log_event(
            "job_completed",
            {"job_id": job.id, "document_id": document.id, "result_id": result.id},
        )
        return True
    except Exception as error:
        if job is not None:
            job_repo.update_job_status(
                db,
                UUID(job.id),
                JobStatus.failed.value,
                str(error),
            )
            log_event("job_failed", {"job_id": job.id, "error": str(error)})
        else:
            log_event("job_failed", {"job_id": None, "error": str(error)})
        return False
