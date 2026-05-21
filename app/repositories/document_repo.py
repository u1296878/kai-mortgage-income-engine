from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import DocumentNotFound
from app.models.document import Document


def save_document(db: Session, document: Document) -> Document:
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_document(db: Session, document_id: UUID) -> Document:
    document = db.get(Document, str(document_id))
    if document is None:
        raise DocumentNotFound(f"Document not found: {document_id}")
    return document


def list_documents_by_case(
    db: Session,
    case_id: UUID,
    broker_id: UUID | None = None,
) -> list[Document]:
    statement = select(Document).where(Document.case_id == str(case_id))
    if broker_id is not None:
        statement = statement.where(Document.broker_id == str(broker_id))
    return list(db.scalars(statement).all())
