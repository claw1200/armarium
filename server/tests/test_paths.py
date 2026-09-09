from pathlib import Path

import pytest

from app.catalog.paths import (
    audio_disk_path,
    file_name,
    media_type_for,
    parent_path,
    parse_file_path,
    parse_folder_path,
)


def test_parse_folder_path_normalizes_root() -> None:
    assert parse_folder_path(None) == ""
    assert parse_folder_path("") == ""
    assert parse_folder_path("/") == ""
    assert parse_folder_path("Drums/Kicks") == "Drums/Kicks"
    assert parse_folder_path("/Drums/Kicks/") == "Drums/Kicks"
    assert parse_folder_path("Drums\\Kicks") == "Drums/Kicks"


def test_parse_folder_path_rejects_parent_segments() -> None:
    with pytest.raises(ValueError, match="inside the library"):
        parse_folder_path("../secret")
    with pytest.raises(ValueError, match="inside the library"):
        parse_folder_path("Drums/../Kicks")


def test_parse_file_path_requires_a_relative_file() -> None:
    assert parse_file_path("Drums/Kicks/kick.wav") == "Drums/Kicks/kick.wav"
    assert parse_file_path("/root.wav") == "root.wav"
    with pytest.raises(ValueError, match="inside the library"):
        parse_file_path("")
    with pytest.raises(ValueError, match="inside the library"):
        parse_file_path("../secret.wav")


def test_media_type_for_known_audio_formats() -> None:
    assert media_type_for("wav") == "audio/wav"
    assert media_type_for("MP3") == "audio/mpeg"
    assert media_type_for("unknown") == "application/octet-stream"


def test_audio_disk_path_stays_inside_the_library(tmp_path: Path) -> None:
    library = tmp_path / "library"
    wav = library / "Drums" / "Kicks" / "kick.wav"
    wav.parent.mkdir(parents=True)
    wav.write_bytes(b"RIFF")
    assert audio_disk_path(library, "Drums/Kicks/kick.wav") == wav.resolve()
    assert audio_disk_path(library, "missing.wav") is None
    assert audio_disk_path(library, "") is None

    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"secret")
    (library / "escape.wav").symlink_to(outside)
    assert audio_disk_path(library, "escape.wav") is None


def test_parent_and_name() -> None:
    assert parent_path("kick.wav") == ""
    assert parent_path("Drums/Kicks/kick.wav") == "Drums/Kicks"
    assert file_name("Drums/Kicks/kick.wav") == "kick.wav"
