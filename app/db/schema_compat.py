from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema_compatibility(engine: Engine) -> None:
    _ensure_user_is_active(engine)
    _ensure_rental_calculation_review_columns(engine)


def _ensure_user_is_active(engine: Engine) -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    column_names = {column["name"] for column in inspector.get_columns("users")}
    if "is_active" in column_names:
        return

    # create_all cannot add columns to existing Railway tables from earlier deploys.
    if engine.dialect.name == "postgresql":
        statement = "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
    else:
        statement = "ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"
    with engine.begin() as connection:
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
