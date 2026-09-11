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


def test_unchanged_rescan_does_not_reread_audio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = write_drum_library(tmp_path / "library")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    assert scan_library(library, store) == 2

    def fail_read(_path: Path) -> None:
        raise AssertionError("unchanged files must not be opened")

    monkeypatch.setattr(scan_module, "read_audio_info", fail_read)
    assert scan_library(library, store) == 2
    kicks = store.list_folder("Drums/Kicks")
    assert kicks.files[0].sample_rate == 44100
    store.close()


def test_rescan_updates_a_changed_file(tmp_path: Path) -> None:
    library = tmp_path / "library"
    path = library / "kick.wav"
    write_sine_wav(path, seconds=0.1)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    original = store.list_folder("").files[0]
    write_sine_wav(path, seconds=0.4, frequency=200)
    assert scan_library(library, store) == 1
    updated = store.list_folder("").files[0]
    assert updated.size_bytes != original.size_bytes
    assert updated.duration_seconds == pytest.approx(0.4, abs=0.02)
    store.close()


def test_rescan_keeps_a_file_when_audio_read_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = tmp_path / "library"
    path = library / "kick.wav"
    write_sine_wav(path, seconds=0.1)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    original = store.list_folder("").files[0]
    write_sine_wav(path, seconds=0.4, frequency=200)

    def fail_read(_path: Path) -> None:
        raise OSError("unreadable")

    monkeypatch.setattr(scan_module, "read_audio_info", fail_read)
    assert scan_library(library, store) == 1
    kept = store.list_folder("").files[0]
    assert kept.relative_path == original.relative_path
    assert kept.duration_seconds == original.duration_seconds
    store.close()


def test_rescan_drops_a_deleted_file(tmp_path: Path) -> None:
    library = write_drum_library(tmp_path / "library")
    extra = library / "gone.wav"
    write_sine_wav(extra)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    assert scan_library(library, store) == 3
    extra.unlink()
    assert scan_library(library, store) == 2
    assert store.get("gone.wav") is None
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
    walked = list(scan_module.iter_audio_files(library))

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
            store.apply_scan(records, [])

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


def test_list_files_pages_and_filters_by_prefix(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Drums" / "Kicks" / "kick.wav")
    write_sine_wav(library / "Drums" / "Snares" / "snare.wav", frequency=180)
    write_sine_wav(library / "Loops" / "Foley" / "fx.wav")
    write_sine_wav(library / "A_" / "Other" / "wild.wav")
    write_sine_wav(library / "AX" / "Leak" / "bad.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)

    page = store.list_files(offset=0, limit=2, sort="path")
    assert page.total == 5
    assert [item.relative_path for item in page.items] == [
        "AX/Leak/bad.wav",
        "A_/Other/wild.wav",
    ]

    drums = store.list_files(offset=0, limit=50, prefix="Drums")
    assert [item.relative_path for item in drums.items] == [
        "Drums/Kicks/kick.wav",
        "Drums/Snares/snare.wav",
    ]

    escaped = store.list_files(offset=0, limit=50, prefix="A_")
    assert [item.relative_path for item in escaped.items] == ["A_/Other/wild.wav"]
    store.close()


def test_list_files_sorts_by_duration_then_path(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "b.wav", seconds=0.2)
    write_sine_wav(library / "a.wav", seconds=0.2)
    write_sine_wav(library / "long.wav", seconds=0.4)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    page = store.list_files(offset=0, limit=50, sort="duration")
    assert [item.name for item in page.items] == ["a.wav", "b.wav", "long.wav"]
    store.close()
