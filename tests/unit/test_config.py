from pathlib import Path

from app.config import Settings


def test_settings_constructs_without_env_file(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("STORAGE_PATH", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///local.db"
    assert settings.storage_path == Path("storage")
    assert settings.jwt_secret_key
    assert settings.app_port == 8000
