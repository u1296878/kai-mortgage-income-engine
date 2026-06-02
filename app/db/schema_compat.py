from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_schema_compatibility(engine: Engine) -> None:
    _ensure_user_is_active(engine)


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
