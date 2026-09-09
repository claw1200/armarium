from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.wav_files import write_sine_wav


@pytest.fixture
def library_root(tmp_path: Path) -> Path:
    root = tmp_path / "library"
    write_sine_wav(root / "Drums" / "Kicks" / "kick.wav")
    write_sine_wav(root / "Drums" / "Snares" / "snare.wav", frequency=180)
    write_sine_wav(root / "root.wav", frequency=440)
    return root


@pytest.fixture
def client(library_root: Path, tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        library_root=library_root,
        database_path=tmp_path / "catalog.sqlite",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client
