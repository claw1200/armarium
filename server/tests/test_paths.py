import pytest

from app.catalog.paths import file_name, parent_path, parse_folder_path


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


def test_parent_and_name() -> None:
    assert parent_path("kick.wav") == ""
    assert parent_path("Drums/Kicks/kick.wav") == "Drums/Kicks"
    assert file_name("Drums/Kicks/kick.wav") == "kick.wav"
