from pathlib import Path

from fastapi.testclient import TestClient

from tests.wav_files import LIBRARY_DIR, write_sine_wav


def _library_file(tmp_path: Path, relative: str) -> Path:
    return tmp_path / LIBRARY_DIR / relative


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


def test_rescan_endpoint_indexes_a_new_file(client: TestClient, tmp_path: Path) -> None:
    write_sine_wav(tmp_path / LIBRARY_DIR / "Drums" / "Hats" / "hat.wav")
    response = client.post("/catalog/scan")
    assert response.status_code == 200
    assert response.json()["file_count"] == 4

    drums = client.get("/catalog/entries", params={"path": "Drums"}).json()
    assert [folder["name"] for folder in drums["folders"]] == ["Hats", "Kicks", "Snares"]


def test_entries_reject_path_escape(client: TestClient) -> None:
    response = client.get("/catalog/entries", params={"path": "../etc"})
    assert response.status_code == 400


def test_catalog_allows_a_browser_origin(client: TestClient) -> None:
    response = client.get("/catalog/entries", headers={"Origin": "http://localhost:1420"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_audio_returns_disk_bytes(client: TestClient, tmp_path: Path) -> None:
    path = _library_file(tmp_path, "Drums/Kicks/kick.wav")
    data = path.read_bytes()
    response = client.get("/audio/Drums/Kicks/kick.wav")
    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["content-disposition"].startswith("inline;")
    assert "kick.wav" in response.headers["content-disposition"]
    assert response.content == data


def test_audio_range_returns_a_byte_slice(client: TestClient, tmp_path: Path) -> None:
    data = _library_file(tmp_path, "Drums/Kicks/kick.wav").read_bytes()
    response = client.get("/audio/Drums/Kicks/kick.wav", headers={"Range": "bytes=0-15"})
    assert response.status_code == 206
    assert response.headers["content-range"] == f"bytes 0-15/{len(data)}"
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == data[:16]


def test_audio_head_reports_size_without_body(client: TestClient, tmp_path: Path) -> None:
    data = _library_file(tmp_path, "Drums/Kicks/kick.wav").read_bytes()
    response = client.head("/audio/Drums/Kicks/kick.wav")
    assert response.status_code == 200
    assert response.headers["accept-ranges"] == "bytes"
    assert int(response.headers["content-length"]) == len(data)
    assert response.content == b""


def test_audio_reads_current_disk_bytes_not_catalog_size(
    client: TestClient, tmp_path: Path
) -> None:
    path = _library_file(tmp_path, "Drums/Kicks/kick.wav")
    original = path.read_bytes()
    write_sine_wav(path, seconds=0.3, frequency=220)
    updated = path.read_bytes()
    assert updated != original
    assert len(updated) != len(original)

    response = client.get("/audio/Drums/Kicks/kick.wav")
    assert response.status_code == 200
    assert response.content == updated
    assert int(response.headers["content-length"]) == len(updated)


def test_audio_streams_a_spaced_filename(client: TestClient, tmp_path: Path) -> None:
    path = _library_file(tmp_path, "Pack/kick 01.wav")
    write_sine_wav(path)
    assert client.post("/catalog/scan").status_code == 200
    response = client.get("/audio/Pack/kick 01.wav")
    assert response.status_code == 200
    assert response.content == path.read_bytes()


def test_audio_rejects_unknown_or_missing_files(client: TestClient, tmp_path: Path) -> None:
    write_sine_wav(_library_file(tmp_path, "unscanned.wav"))
    missing = client.get("/audio/unscanned.wav")
    assert missing.status_code == 404

    _library_file(tmp_path, "root.wav").unlink()
    gone = client.get("/audio/root.wav")
    assert gone.status_code == 404


def test_audio_rejects_path_escape(client: TestClient) -> None:
    response = client.get("/audio/Drums/%2e%2e/secret.wav")
    assert response.status_code == 400
