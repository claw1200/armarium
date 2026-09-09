from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.catalog.store import CatalogStore
from app.indexer import scan as scan_module
from app.indexer.scan import scan_library
from tests.wav_files import write_drum_library, write_sine_wav


def test_scan_indexes_nested_audio_and_skips_other_files(tmp_path: Path) -> None:
    library = write_drum_library(tmp_path / "library")
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


def test_scan_skips_a_vanished_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    library = write_drum_library(tmp_path / "library")
    vanished = library / "gone.wav"
    write_sine_wav(vanished)
    walked = scan_module.iter_audio_files(library)

    def after_unlink(_library_root: Path) -> list[Path]:
        vanished.unlink()
        return walked

    monkeypatch.setattr(scan_module, "iter_audio_files", after_unlink)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    assert scan_library(library, store) == 2
    store.close()


def test_scan_skips_a_symlink_outside_the_library(tmp_path: Path) -> None:
    library = write_drum_library(tmp_path / "library")
    outside = tmp_path / "outside.wav"
    write_sine_wav(outside)
    (library / "escape.wav").symlink_to(outside)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    assert scan_library(library, store) == 2
    store.close()


def test_store_serializes_concurrent_reads_and_writes(tmp_path: Path) -> None:
    library = write_drum_library(tmp_path / "library")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    records = store.list_folder("Drums/Kicks").files

    def read_repeatedly() -> None:
        for _ in range(40):
            store.list_folder("")

    def write_repeatedly() -> None:
        for _ in range(20):
            store.replace_all(records)

    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(read_repeatedly) for _ in range(3)]
        jobs.append(pool.submit(write_repeatedly))
        for job in jobs:
            job.result()
    store.close()


def test_list_folder_does_not_include_unrelated_trees(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Drums" / "Kicks" / "kick.wav")
    write_sine_wav(library / "Loops" / "Foley" / "fx.wav")
    write_sine_wav(library / "A_" / "Other" / "wild.wav")
    write_sine_wav(library / "AX" / "Leak" / "bad.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    assert [folder.name for folder in store.list_folder("Drums").folders] == ["Kicks"]
    assert [folder.name for folder in store.list_folder("A_").folders] == ["Other"]
    assert [folder.name for folder in store.list_folder("AX").folders] == ["Leak"]
    store.close()
