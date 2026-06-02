from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.exceptions import JobAlreadyProcessed, JobNotFound
from app.models.user import User
from app.schemas.job import JobStatusResponse
from app.services import job_service

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JobStatusResponse:
    try:
        return job_service.get_job_status(db, job_id, current_user)
    except JobNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/documents/{document_id}/job", response_model=JobStatusResponse)
def get_document_job(
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JobStatusResponse:
    try:
        return job_service.get_job_for_document(db, document_id, current_user)
    except JobNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/jobs/{job_id}/retry", response_model=JobStatusResponse)
def retry_job(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> JobStatusResponse:
    try:
        return job_service.retry_job(db, job_id, current_user)
    except JobNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except JobAlreadyProcessed as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
