from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema_compatibility(engine: Engine) -> None:
    _remove_hosted_auth_artifacts(engine)
    _ensure_job_progress_columns(engine)
    _ensure_rental_calculation_review_columns(engine)
    _ensure_self_employment_review_columns(engine)


def _remove_hosted_auth_artifacts(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "cases" in table_names and _has_column(inspector, "cases", "broker_id"):
        _remove_cases_broker_id(engine)
    if "documents" in table_names and _has_column(inspector, "documents", "broker_id"):
        _remove_documents_broker_id(engine)
    if "users" in table_names:
        _execute_statements(engine, ["DROP TABLE users"])


def _remove_cases_broker_id(engine: Engine) -> None:
    if engine.dialect.name == "sqlite":
        _rebuild_sqlite_table(
            engine,
            "cases",
            """
            CREATE TABLE __cases_local (
                id VARCHAR(36) NOT NULL,
                title VARCHAR NOT NULL,
                status VARCHAR NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
            """,
            ("id", "title", "status", "created_at", "updated_at"),
        )
        return
    _execute_statements(engine, ["ALTER TABLE cases DROP COLUMN broker_id"])


def _remove_documents_broker_id(engine: Engine) -> None:
    if engine.dialect.name == "sqlite":
        _rebuild_sqlite_table(
            engine,
            "documents",
            """
            CREATE TABLE __documents_local (
                id VARCHAR(36) NOT NULL,
                filename VARCHAR NOT NULL,
                doc_type VARCHAR NOT NULL,
                storage_path VARCHAR NOT NULL,
                case_id VARCHAR(36),
                uploaded_at DATETIME NOT NULL,
                PRIMARY KEY (id)
            )
            """,
            ("id", "filename", "doc_type", "storage_path", "case_id", "uploaded_at"),
        )
        return
    _execute_statements(engine, ["ALTER TABLE documents DROP COLUMN broker_id"])


def _rebuild_sqlite_table(
    engine: Engine,
    table_name: str,
    create_statement: str,
    columns: tuple[str, ...],
) -> None:
    temp_name = f"__{table_name}_local"
    column_list = ", ".join(columns)
    statements = [
        f"DROP TABLE IF EXISTS {temp_name}",
        create_statement,
        f"INSERT INTO {temp_name} ({column_list}) SELECT {column_list} FROM {table_name}",
        f"DROP TABLE {table_name}",
        f"ALTER TABLE {temp_name} RENAME TO {table_name}",
    ]
    _execute_statements(engine, statements)


def _execute_statements(engine: Engine, statements: list[str]) -> None:
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _ensure_job_progress_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return
    column_names = {column["name"] for column in inspector.get_columns("jobs")}
    statements = []
    if "pages_total" not in column_names:
        statements.append(_add_column(engine, "jobs", "pages_total INTEGER NOT NULL DEFAULT 0"))
    if "pages_done" not in column_names:
        statements.append(_add_column(engine, "jobs", "pages_done INTEGER NOT NULL DEFAULT 0"))
    if "current_stage" not in column_names:
        statements.append(_add_column(engine, "jobs", "current_stage VARCHAR"))
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _ensure_rental_calculation_review_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "rental_calculations" not in inspector.get_table_names():
        return
    column_names = {column["name"] for column in inspector.get_columns("rental_calculations")}
    statements = []
    if "included" not in column_names:
        default = "TRUE" if engine.dialect.name == "postgresql" else "1"
        statements.append(f"ALTER TABLE rental_calculations ADD COLUMN included BOOLEAN NOT NULL DEFAULT {default}")
    if "source_document_id" not in column_names:
        statements.append("ALTER TABLE rental_calculations ADD COLUMN source_document_id VARCHAR(36)")
    if "source_property_key" not in column_names:
        statements.append("ALTER TABLE rental_calculations ADD COLUMN source_property_key VARCHAR")
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _add_column(engine: Engine, table: str, column_definition: str) -> str:
    if engine.dialect.name == "postgresql":
        return f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column_definition}"
    return f"ALTER TABLE {table} ADD COLUMN {column_definition}"


def _ensure_self_employment_review_columns(engine: Engine) -> None:
    inspector = inspect(engine)
    if "self_employment_calculations" not in inspector.get_table_names():
        return
    column_names = {column["name"] for column in inspector.get_columns("self_employment_calculations")}
    statements = []
    if "included" not in column_names:
        default = "TRUE" if engine.dialect.name == "postgresql" else "1"
        statements.append(f"ALTER TABLE self_employment_calculations ADD COLUMN included BOOLEAN NOT NULL DEFAULT {default}")
    if "source_document_id" not in column_names:
        statements.append("ALTER TABLE self_employment_calculations ADD COLUMN source_document_id VARCHAR(36)")
    if "source_business_key" not in column_names:
        statements.append("ALTER TABLE self_employment_calculations ADD COLUMN source_business_key VARCHAR")
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
