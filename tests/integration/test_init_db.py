from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, MetaData, String, Table
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.db import init_db as init_db_module


def test_init_db_registers_current_models(monkeypatch):
    engine = _create_test_engine()
    monkeypatch.setattr(init_db_module, "engine", engine)

    init_db_module.init_db()

    inspector = inspect(engine)
    assert {"users", "borrowers", "income_streams"}.issubset(inspector.get_table_names())
    user_columns = _column_names(engine, "users")
    assert "is_active" in user_columns


def test_init_db_adds_is_active_to_existing_users_table(monkeypatch):
    engine = _create_test_engine()
    _create_legacy_users_table(engine)
    monkeypatch.setattr(init_db_module, "engine", engine)

    init_db_module.init_db()

    assert "is_active" in _column_names(engine, "users")
    with engine.connect() as connection:
        value = connection.execute(text("SELECT is_active FROM users")).scalar_one()
    assert value in (True, 1)


def test_init_db_adds_progress_to_existing_jobs_table(monkeypatch):
    engine = _create_test_engine()
    _create_legacy_jobs_table(engine)
    monkeypatch.setattr(init_db_module, "engine", engine)

    init_db_module.init_db()

    columns = _column_names(engine, "jobs")
    assert {"pages_total", "pages_done", "current_stage"} <= columns
    with engine.connect() as connection:
        row = connection.execute(text("SELECT pages_total, pages_done, current_stage FROM jobs")).one()
    assert tuple(row) == (0, 0, None)


def _create_test_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _create_legacy_users_table(engine) -> None:
    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("email", String, nullable=False),
        Column("hashed_password", String, nullable=False),
        Column("role", String, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
    )
    metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            users.insert().values(
                id="legacy-user",
                email="broker@example.com",
                hashed_password="hashed",
                role="broker",
                created_at=datetime.now(timezone.utc),
            ),
        )


def _create_legacy_jobs_table(engine) -> None:
    metadata = MetaData()
    jobs = Table(
        "jobs",
        metadata,
        Column("id", String(36), primary_key=True),
        Column("document_id", String(36), nullable=False),
        Column("status", String, nullable=False),
        Column("error", String, nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("started_at", DateTime(timezone=True), nullable=True),
        Column("completed_at", DateTime(timezone=True), nullable=True),
    )
    metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(
            jobs.insert().values(
                id="legacy-job",
                document_id="legacy-document",
                status="pending",
                created_at=datetime.now(timezone.utc),
            ),
        )


def _column_names(engine, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}
