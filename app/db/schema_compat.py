from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema_compatibility(engine: Engine) -> None:
    _ensure_job_progress_columns(engine)
    _ensure_rental_calculation_review_columns(engine)
    _ensure_self_employment_review_columns(engine)


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
