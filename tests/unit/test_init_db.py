from pathlib import Path

from app.db import init_db


def test_sqlite_parent_directory_is_created(tmp_path, monkeypatch):
    database_path = tmp_path / "nested" / "kai.db"
    monkeypatch.setattr(
        init_db.settings,
        "database_url",
        f"sqlite:///{database_path.as_posix()}",
    )

    init_db._ensure_sqlite_parent_exists()

    assert database_path.parent.exists()
