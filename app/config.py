from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")

    database_url: str = "sqlite:///./local.db"
    storage_path: str = "./storage"


settings = Settings()
