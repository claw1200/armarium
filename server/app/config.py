from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    library_root: Path = Path("/library")
    database_path: Path = Path("/data/catalog.sqlite")
