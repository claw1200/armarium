from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
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
    assert kicks["files"][0]["parent_path"] == "Drums/Kicks"
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


def test_files_lists_the_library_in_path_order(client: TestClient) -> None:
    response = client.get("/catalog/files")
    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 3
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert [item["path"] for item in body["items"]] == [
        "Drums/Kicks/kick.wav",
        "Drums/Snares/snare.wav",
        "root.wav",
    ]
    assert body["items"][0]["parent_path"] == "Drums/Kicks"
    assert body["items"][2]["parent_path"] == ""


def test_files_paginates_without_changing_total(client: TestClient) -> None:
    first = client.get("/catalog/files", params={"limit": 1, "offset": 0}).json()
    second = client.get("/catalog/files", params={"limit": 1, "offset": 1}).json()
    assert first["total"] == 3
    assert second["total"] == 3
    assert [item["path"] for item in first["items"]] == ["Drums/Kicks/kick.wav"]
    assert [item["path"] for item in second["items"]] == ["Drums/Snares/snare.wav"]


def test_files_prefix_includes_nested_folder_not_siblings(client: TestClient) -> None:
    drums = client.get("/catalog/files", params={"prefix": "Drums"}).json()
    assert [item["path"] for item in drums["items"]] == [
        "Drums/Kicks/kick.wav",
        "Drums/Snares/snare.wav",
    ]
    assert drums["total"] == 2


def test_files_sorts_by_name(client: TestClient) -> None:
    body = client.get("/catalog/files", params={"sort": "name"}).json()
    assert [item["name"] for item in body["items"]] == ["kick.wav", "root.wav", "snare.wav"]


def test_files_filters_by_path_substring(client: TestClient) -> None:
    kicks = client.get("/catalog/files", params={"q": "KICK"}).json()
    assert [item["path"] for item in kicks["items"]] == ["Drums/Kicks/kick.wav"]
    assert kicks["total"] == 1
    drums = client.get("/catalog/files", params={"q": " drums "}).json()
    assert [item["path"] for item in drums["items"]] == [
        "Drums/Kicks/kick.wav",
        "Drums/Snares/snare.wav",
    ]
    missing = client.get("/catalog/files", params={"q": "nope"}).json()
    assert missing == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_files_rejects_invalid_query(client: TestClient) -> None:
    assert client.get("/catalog/files", params={"limit": 201}).status_code == 400
    assert client.get("/catalog/files", params={"limit": 0}).status_code == 400
    assert client.get("/catalog/files", params={"offset": -1}).status_code == 400
    assert client.get("/catalog/files", params={"sort": "bpm"}).status_code == 400
    assert client.get("/catalog/files", params={"prefix": "../etc"}).status_code == 400
    assert client.get("/catalog/files", params={"q": "x" * 201}).status_code == 400


def test_files_empty_library(tmp_path: Path) -> None:
    (tmp_path / LIBRARY_DIR).mkdir()
    settings = Settings(
        library_root=tmp_path / LIBRARY_DIR,
        database_path=tmp_path / "catalog.sqlite",
    )
    with TestClient(create_app(settings)) as empty_client:
        body = empty_client.get("/catalog/files").json()
    assert body == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_entries_reject_path_escape(client: TestClient) -> None:
    response = client.get("/catalog/entries", params={"path": "../etc"})
    assert response.status_code == 400


def test_catalog_allows_a_configured_origin(client: TestClient) -> None:
    response = client.get("/catalog/entries", headers={"Origin": "http://localhost:1420"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:1420"


def test_catalog_omits_cors_for_an_unknown_origin(client: TestClient) -> None:
    response = client.get("/catalog/entries", headers={"Origin": "https://evil.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


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
