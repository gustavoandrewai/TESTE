from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FII Asymmetry Analyzer"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/fii_db"
    scheduler_enabled: bool = False
    data_provider: str = "mock"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
