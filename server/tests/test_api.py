from pathlib import Path

from fastapi.testclient import TestClient

from tests.wav_files import write_sine_wav


def test_startup_scan_lists_nested_library(client: TestClient) -> None:
    root = client.get("/catalog/entries").json()
    assert root["path"] == ""
    assert [folder["name"] for folder in root["folders"]] == ["Drums"]
    assert [file["name"] for file in root["files"]] == ["root.wav"]

    drums = client.get("/catalog/entries", params={"path": "Drums"}).json()
    assert [folder["path"] for folder in drums["folders"]] == ["Drums/Kicks", "Drums/Snares"]
    assert drums["files"] == []

    kicks = client.get("/catalog/entries", params={"path": "Drums/Kicks"}).json()
    assert kicks["folders"] == []
    assert kicks["files"][0]["name"] == "kick.wav"
    assert kicks["files"][0]["path"] == "Drums/Kicks/kick.wav"
    assert kicks["files"][0]["format"] == "wav"
    assert kicks["files"][0]["sample_rate"] == 44100
    assert kicks["files"][0]["channels"] == 1
    assert kicks["files"][0]["duration_seconds"] is not None


def test_rescan_endpoint_indexes_a_new_file(client: TestClient, library_root: Path) -> None:
    write_sine_wav(library_root / "Drums" / "Hats" / "hat.wav")
    response = client.post("/catalog/scan")
    assert response.status_code == 200
    assert response.json()["file_count"] == 4

    drums = client.get("/catalog/entries", params={"path": "Drums"}).json()
    assert [folder["name"] for folder in drums["folders"]] == ["Hats", "Kicks", "Snares"]


def test_entries_reject_path_escape(client: TestClient) -> None:
    response = client.get("/catalog/entries", params={"path": "../etc"})
    assert response.status_code == 400
