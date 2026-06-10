from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.exceptions import CaseNotFound
from app.runtime.local_user import LOCAL_USER_ID
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate, CaseWithDocuments
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse)
def create_case(
    case: CaseCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CaseResponse:
    return case_service.create_case(db, case.title, LOCAL_USER_ID)


@router.get("", response_model=list[CaseResponse])
def list_cases(
    db: Annotated[Session, Depends(get_db)],
) -> list[CaseResponse]:
    return case_service.list_cases(db, LOCAL_USER_ID)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CaseResponse:
    try:
        return case_service.get_case(db, case_id, LOCAL_USER_ID)
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{case_id}/documents", response_model=CaseWithDocuments)
def get_case_with_documents(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CaseWithDocuments:
    try:
        return case_service.get_case_with_documents(
            db,
            case_id,
            LOCAL_USER_ID,
        )
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: UUID,
    updates: CaseUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> CaseResponse:
    try:
        update_values = updates.model_dump(exclude_none=True)
        return case_service.update_case(db, case_id, update_values, LOCAL_USER_ID)
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/{case_id}", status_code=204)
def delete_case(
    case_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        case_service.delete_case(db, case_id, LOCAL_USER_ID)
    except CaseNotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=204)
