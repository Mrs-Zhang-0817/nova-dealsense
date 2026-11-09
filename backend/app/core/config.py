from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore")
    app_name: str = "NOVA DealSense"
    database_url: str
    frontend_origin: str = "http://localhost:3000"

settings = Settings()
