from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.runtime.app_paths import app_data_dir


def _default_database_url() -> str:
    database_path = app_data_dir() / "local.db"
    return f"sqlite:///{database_path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    database_url: str = Field(default_factory=_default_database_url)
    storage_path: Path = Field(default_factory=lambda: app_data_dir() / "storage")
    worker_poll_interval: int = 5
    app_port: int = 8000
    no_browser: bool = False
    allowed_origins: str = "*"
    ocr_dpi: int = 150
    ocr_max_workers: int = 4
    ocr_page_timeout_seconds: int = 60
    ocr_thread_limit: int = 1
    tesseract_cmd: Path | None = None
    extraction_backend: Literal["rules", "model"] = "rules"
    extraction_provider: Literal["anthropic", "ollama"] = "anthropic"
    extraction_confidence_threshold: float = 0.5
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_temperature: float = 0.0
    ollama_num_ctx: int = 4096
    ollama_num_gpu: int | None = None


settings = Settings()
