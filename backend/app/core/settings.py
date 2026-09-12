from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    youtube_api_key: str | None = None
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lajme_prime"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
