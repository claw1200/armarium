from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.wav_files import LIBRARY_DIR, write_example_library


def test_cors_origins_parse_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", '["http://ui:5173"]')
    assert Settings().cors_origins == ["http://ui:5173"]


def test_custom_cors_origin_is_allowed(tmp_path: Path) -> None:
    settings = Settings(
        library_root=write_example_library(tmp_path / LIBRARY_DIR),
        database_path=tmp_path / "catalog.sqlite",
        cors_origins=["http://ui:5173"],
    )
    with TestClient(create_app(settings)) as client:
        allowed = client.get("/catalog/entries", headers={"Origin": "http://ui:5173"})
        denied = client.get("/catalog/entries", headers={"Origin": "http://localhost:1420"})
    assert allowed.headers["access-control-allow-origin"] == "http://ui:5173"
    assert "access-control-allow-origin" not in denied.headers
