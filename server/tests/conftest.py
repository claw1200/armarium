from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.wav_files import LIBRARY_DIR, write_example_library


def wait_until_idle(api: TestClient) -> None:
    with api.websocket_connect("/catalog/scan") as socket:
        while socket.receive_json()["status"] != "idle":
            pass


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        library_root=write_example_library(tmp_path / LIBRARY_DIR),
        database_path=tmp_path / "catalog.sqlite",
    )
    with TestClient(create_app(settings)) as test_client:
        wait_until_idle(test_client)
        yield test_client
