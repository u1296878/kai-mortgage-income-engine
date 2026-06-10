from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    database_path = Path("local.db")
    return f"sqlite:///{database_path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    database_url: str = _default_database_url()
    storage_path: Path = Path("storage")
    worker_poll_interval: int = 5
    app_port: int = 8000
    no_browser: bool = False
    allowed_origins: str = "*"
    # TODO step 2: remove with auth.
    jwt_secret_key: str = "local-development-only-jwt-secret-change-after-auth-removal"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    manager_email: str | None = None
    manager_password: str | None = None
    ocr_dpi: int = 150
    ocr_max_workers: int = 4
    ocr_page_timeout_seconds: int = 60
    ocr_thread_limit: int = 1


settings = Settings()
