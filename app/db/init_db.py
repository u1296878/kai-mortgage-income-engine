from pathlib import Path

from sqlalchemy.engine import make_url

from app.config import settings
from app.db.base import Base
from app.db.schema_compat import ensure_schema_compatibility
from app.db.session import engine
from app import models  # noqa: F401


def init_db() -> None:
    _ensure_sqlite_parent_exists()
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)


def _ensure_sqlite_parent_exists() -> None:
    url = make_url(settings.database_url)
    if not url.drivername.startswith("sqlite"):
        return
    if url.database in (None, "", ":memory:"):
        return

    Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)
