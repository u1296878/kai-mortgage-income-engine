from app.db.base import Base
from app.db.schema_compat import ensure_schema_compatibility
from app.db.session import engine
from app import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
