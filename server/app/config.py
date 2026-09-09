from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:1420",
    "http://localhost:1420",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    library_root: Path = Path("/library")
    database_path: Path = Path("/data/catalog.sqlite")
    cors_origins: list[str] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
