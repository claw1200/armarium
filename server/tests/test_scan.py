from pathlib import Path

from app.catalog.store import CatalogStore
from app.indexer.scan import scan_library
from tests.wav_files import write_sine_wav


def test_scan_indexes_nested_audio_and_skips_other_files(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Drums" / "Kicks" / "kick.wav")
    write_sine_wav(library / "Drums" / "Snares" / "snare.wav")
    (library / "readme.txt").write_text("ignore", encoding="utf-8")
    (library / ".hidden.wav").write_text("ignore", encoding="utf-8")

    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    assert scan_library(library, store) == 2

    root = store.list_folder("")
    assert [folder.name for folder in root.folders] == ["Drums"]
    assert [file.name for file in root.files] == []

    drums = store.list_folder("Drums")
    assert [folder.name for folder in drums.folders] == ["Kicks", "Snares"]
    assert not drums.files

    kicks = store.list_folder("Drums/Kicks")
    assert not kicks.folders
    assert [file.name for file in kicks.files] == ["kick.wav"]
    assert kicks.files[0].format == "wav"
    assert kicks.files[0].sample_rate == 44100
    store.close()


def test_rescan_picks_up_a_new_file(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Drums" / "Kicks" / "kick.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)

    write_sine_wav(library / "Drums" / "Hats" / "hat.wav")
    scan_library(library, store)
    drums = store.list_folder("Drums")
    assert [folder.name for folder in drums.folders] == ["Hats", "Kicks"]
    store.close()
