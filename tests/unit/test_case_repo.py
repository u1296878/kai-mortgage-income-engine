from uuid import uuid4

from app.models.case import Case
from app.repositories import case_repo


def test_find_case_returns_case_when_present(test_db):
    case = Case(id=str(uuid4()), broker_id=str(uuid4()), title="Smith Purchase")
    test_db.add(case)
    test_db.commit()

    result = case_repo.find_case(test_db, case.id)

    assert result.id == case.id


def test_find_case_returns_none_when_missing(test_db):
    result = case_repo.find_case(test_db, uuid4())

    assert result is None
