from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    database_url: str = "sqlite:///./local.db"
    storage_path: str = "./storage"
    worker_poll_interval: int = 5
    jwt_secret_key: str = "local-development-secret-change-before-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60


settings = Settings()
