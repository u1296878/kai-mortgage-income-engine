from pathlib import Path

from app import config
from app.config import Settings


def test_settings_constructs_without_env_file(monkeypatch):
    data_dir = Path("C:/Users/example/AppData/Local/KaiMortgageIncomeEngine")
    monkeypatch.setattr(config, "app_data_dir", lambda: data_dir)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("STORAGE_PATH", raising=False)

    settings = Settings(_env_file=None)

    assert settings.database_url == "sqlite:///C:/Users/example/AppData/Local/KaiMortgageIncomeEngine/local.db"
    assert settings.storage_path == data_dir / "storage"
    assert settings.app_port == 8000


def test_default_data_paths_are_outside_repo(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("STORAGE_PATH", raising=False)

    settings = Settings(_env_file=None)
    repo_root = Path.cwd().resolve()
    database_path = Path(settings.database_url.removeprefix("sqlite:///")).resolve()

    assert not database_path.is_relative_to(repo_root)
    assert not settings.storage_path.resolve().is_relative_to(repo_root)
