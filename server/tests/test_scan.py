from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from app.catalog.store import CatalogStore
from app.indexer import scan as scan_module
from app.indexer.form import FormEstimate
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

    kicks = store.list_files(offset=0, limit=50, query="kick")
    assert [item.relative_path for item in kicks.items] == ["Drums/Kicks/kick.wav"]
    drums = store.list_files(offset=0, limit=50, query="DRUMS")
    assert [item.relative_path for item in drums.items] == [
        "Drums/Kicks/kick.wav",
        "Drums/Snares/snare.wav",
    ]
    wildcard = store.list_files(offset=0, limit=50, query="A_")
    assert [item.relative_path for item in wildcard.items] == ["A_/Other/wild.wav"]
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


def test_scan_infers_bpm_and_key_from_the_filename(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Loop_128bpm_Cmin.wav")
    write_sine_wav(library / "808_snare.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    loop = store.get_meta("Loop_128bpm_Cmin.wav")
    assert loop is not None
    assert loop.bpm_inferred == 128
    assert loop.key_inferred == "Cm"
    assert loop.bpm_user is None
    assert store.get_meta("808_snare.wav") is None
    assert store.tags_by_paths(["Loop_128bpm_Cmin.wav"])["Loop_128bpm_Cmin.wav"] == ["one-shot"]
    assert store.tags_by_paths(["808_snare.wav"])["808_snare.wav"] == ["one-shot", "snare"]
    store.close()


def test_rescan_refreshes_inferred_meta_without_opening_audio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Loop_128bpm_Cmin.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    store.set_user("Loop_128bpm_Cmin.wav", bpm=130, key="Dm")

    def fail_read(_path: Path) -> None:
        raise AssertionError("unchanged files must not be opened")

    monkeypatch.setattr(scan_module, "read_audio_info", fail_read)
    assert scan_library(library, store) == 1
    meta = store.get_meta("Loop_128bpm_Cmin.wav")
    assert meta is not None
    assert meta.bpm_inferred == 128
    assert meta.key_inferred == "Cm"
    assert meta.bpm_user == 130
    assert meta.key_user == "Dm"
    store.close()


def test_scan_writes_inferred_tags_and_keeps_user_overlay(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Drums" / "Kicks" / "kick.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    assert store.tags_by_paths(["Drums/Kicks/kick.wav"])["Drums/Kicks/kick.wav"] == [
        "one-shot",
        "kick",
    ]
    store.set_user_tag("Drums/Kicks/kick.wav", "kick", present=False)
    store.set_user_tag("Drums/Kicks/kick.wav", "perc", present=True)
    assert store.tags_by_paths(["Drums/Kicks/kick.wav"])["Drums/Kicks/kick.wav"] == [
        "one-shot",
        "perc",
    ]
    scan_library(library, store)
    assert store.tags_by_paths(["Drums/Kicks/kick.wav"])["Drums/Kicks/kick.wav"] == [
        "one-shot",
        "perc",
    ]
    store.close()


def test_scan_runs_estimator_only_on_changed_wavs(tmp_path: Path) -> None:
    library = tmp_path / "library"
    path = library / "phrase.wav"
    write_sine_wav(path, seconds=1.0)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    calls: list[str] = []

    def estimator(audio_path: Path) -> FormEstimate:
        calls.append(audio_path.name)
        return FormEstimate(is_loop=True, bpm=128)

    scan_library(library, store, form_estimator=estimator)
    scan_library(library, store, form_estimator=estimator)
    assert calls == ["phrase.wav"]
    meta = store.get_meta("phrase.wav")
    assert meta is not None
    assert meta.audio_is_loop is True
    assert meta.audio_bpm == 128
    assert meta.bpm_inferred == 128
    assert store.tags_by_paths(["phrase.wav"])["phrase.wav"] == ["loop"]
    write_sine_wav(path, seconds=1.2, frequency=200)
    scan_library(library, store, form_estimator=estimator)
    assert calls == ["phrase.wav", "phrase.wav"]
    store.close()


def test_scan_skips_estimator_for_short_files(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "hat.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()

    def fail_estimator(_path: Path) -> FormEstimate:
        raise AssertionError("short files must not be analyzed")

    scan_library(library, store, form_estimator=fail_estimator)
    assert store.tags_by_paths(["hat.wav"])["hat.wav"] == ["one-shot", "hat"]
    store.close()


def test_scan_uses_path_form_when_duration_is_ambiguous(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Loops" / "Melodic" / "synth_lead.wav", seconds=2.0)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store, form_estimator=lambda _path: FormEstimate(None, None))
    assert store.tags_by_paths(["Loops/Melodic/synth_lead.wav"])[
        "Loops/Melodic/synth_lead.wav"
    ] == ["loop", "synth", "melody"]
    store.close()
