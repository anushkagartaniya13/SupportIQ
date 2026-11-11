from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    database_path: str = "./data/supportiq.db"
    confidence_threshold: float = 0.18
    max_upload_bytes: int = 2_000_000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
