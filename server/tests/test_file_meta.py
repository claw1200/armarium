import os
import sqlite3
import time
from pathlib import Path

import pytest

from app.catalog.meta import (
    CANONICAL_KEYS,
    check_bpm,
    check_key,
    key_filter_values,
    parse_bpm_range,
)
from app.catalog.store import RECENT_WINDOW_NS, CatalogStore
from app.indexer.form import FormEstimate
from app.indexer.scan import scan_library
from tests.wav_files import write_sine_wav

_KICK = "kick.wav"


def _store_with_kick(tmp_path: Path) -> CatalogStore:
    write_sine_wav(tmp_path / "library" / _KICK)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(tmp_path / "library", store)
    return store


def test_canonical_keys_are_the_24_sharp_spellings() -> None:
    assert len(CANONICAL_KEYS) == 24
    assert "C" in CANONICAL_KEYS
    assert "C#m" in CANONICAL_KEYS
    assert "Bm" in CANONICAL_KEYS
    assert "Db" not in CANONICAL_KEYS
    assert "Am" in CANONICAL_KEYS
    assert "Amin" not in CANONICAL_KEYS


def test_key_filter_matches_a_pitch_class_or_an_exact_key() -> None:
    assert key_filter_values("C") == ("C", "Cm")
    assert key_filter_values("F#") == ("F#", "F#m")
    assert key_filter_values("Cm") == ("Cm",)
    with pytest.raises(ValueError, match="invalid key"):
        key_filter_values("Db")


def test_parse_bpm_range_uses_inclusive_min_and_exclusive_max() -> None:
    assert parse_bpm_range("70-90") == (70.0, 90.0)
    assert parse_bpm_range("150+") == (150.0, None)
    with pytest.raises(ValueError, match="invalid bpm"):
        parse_bpm_range("70–90")


def test_check_bpm_and_key_reject_invalid_values() -> None:
    check_bpm(None)
    check_bpm(87.5)
    check_bpm(400)
    with pytest.raises(ValueError, match="invalid bpm"):
        check_bpm(0)
    with pytest.raises(ValueError, match="invalid bpm"):
        check_bpm(-1)
    with pytest.raises(ValueError, match="invalid bpm"):
        check_bpm(400.1)
    check_key(None)
    check_key("F#m")
    with pytest.raises(ValueError, match="invalid key"):
        check_key("Db")
    with pytest.raises(ValueError, match="invalid key"):
        check_key("Amin")


def test_missing_meta_row_is_unknown(tmp_path: Path) -> None:
    store = _store_with_kick(tmp_path)
    assert store.get(_KICK) is not None
    assert store.get_meta(_KICK) is None
    store.close()


def test_file_meta_expression_indexes_exist(tmp_path: Path) -> None:
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    store.close()
    with sqlite3.connect(tmp_path / "catalog.sqlite") as connection:
        index_sql = (
            "SELECT name, sql FROM sqlite_master "
            "WHERE type = 'index' AND tbl_name = 'file_meta'"
        )
        indexes = dict(connection.execute(index_sql))
    assert "coalesce(bpm_user, bpm_inferred)" in indexes["file_meta_bpm"].lower()
    assert "coalesce(key_user, key_inferred)" in indexes["file_meta_key"].lower()


def test_user_values_override_inferred_and_clearing_restores_them(tmp_path: Path) -> None:
    store = _store_with_kick(tmp_path)
    inferred = store.set_inferred(_KICK, bpm=128, key="Cm")
    assert inferred.bpm == 128
    assert inferred.key == "Cm"
    assert inferred.bpm_user is None
    assert inferred.key_user is None

    overridden = store.set_user(_KICK, bpm=140, key="Dm")
    assert overridden.bpm == 140
    assert overridden.key == "Dm"
    assert overridden.bpm_inferred == 128
    assert overridden.key_inferred == "Cm"

    store.set_user(_KICK, bpm=None)
    partial = store.get_meta(_KICK)
    assert partial is not None
    assert partial.bpm == 128
    assert partial.key == "Dm"

    restored = store.set_user(_KICK, key=None)
    assert restored.bpm == 128
    assert restored.key == "Cm"
    assert restored.bpm_user is None
    assert restored.key_user is None
    store.close()


def test_file_upsert_does_not_clobber_user_meta(tmp_path: Path) -> None:
    store = _store_with_kick(tmp_path)
    store.set_inferred(_KICK, bpm=128, key="C")
    store.set_user(_KICK, bpm=90, key="Am")
    record = store.get(_KICK)
    assert record is not None
    assert store.apply_scan([record], []) == 1
    meta = store.get_meta(_KICK)
    assert meta is not None
    assert meta.bpm_user == 90
    assert meta.key_user == "Am"
    assert meta.bpm_inferred == 128
    assert meta.key_inferred == "C"
    store.close()


def test_rescan_of_a_changed_file_keeps_user_meta(tmp_path: Path) -> None:
    library = tmp_path / "library"
    path = library / _KICK
    write_sine_wav(path, seconds=0.1)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store)
    store.set_inferred(_KICK, bpm=120, key="F#m")
    store.set_user(_KICK, bpm=118)
    write_sine_wav(path, seconds=0.4, frequency=200)
    assert scan_library(library, store) == 1
    meta = store.get_meta(_KICK)
    assert meta is not None
    assert meta.bpm_user == 118
    assert meta.bpm_inferred is None
    assert meta.key_inferred is None
    assert meta.bpm == 118
    store.close()


def test_deleting_a_file_cascades_meta(tmp_path: Path) -> None:
    store = _store_with_kick(tmp_path)
    store.set_inferred(_KICK, bpm=128, key="C")
    store.set_user(_KICK, bpm=132)
    assert store.apply_scan([], [_KICK]) == 0
    assert store.get(_KICK) is None
    assert store.get_meta(_KICK) is None
    store.close()


def test_meta_writes_require_a_known_file_and_a_field(tmp_path: Path) -> None:
    store = _store_with_kick(tmp_path)
    with pytest.raises(LookupError):
        store.set_inferred("missing.wav", bpm=120)
    with pytest.raises(TypeError, match="bpm or key"):
        store.set_inferred(_KICK)
    with pytest.raises(ValueError, match="invalid bpm"):
        store.set_user(_KICK, bpm=0)
    with pytest.raises(ValueError, match="invalid key"):
        store.set_inferred(_KICK, key="Db")
    assert store.get_meta(_KICK) is None
    store.close()


def test_user_tag_overlay_survives_and_cascades(tmp_path: Path) -> None:
    store = _store_with_kick(tmp_path)
    store.set_user_tag(_KICK, "kick", present=False)
    store.set_user_tag(_KICK, "fx", present=True)
    assert store.tags_by_paths([_KICK])[_KICK] == ["one-shot", "fx"]
    assert store.apply_scan([], [_KICK]) == 0
    assert store.tags_by_paths([_KICK])[_KICK] == []
    store.close()


def test_list_files_filters_by_all_requested_tags(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Drums" / "Kicks" / "kick.wav")
    write_sine_wav(library / "Drums" / "Hats" / "hat.wav")
    write_sine_wav(library / "Loops" / "Melodic" / "synth_lead.wav", seconds=2.0)
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store, form_estimator=lambda _path: FormEstimate(None, None))
    kicks = store.list_files(offset=0, limit=50, tags=["kick"])
    assert [item.relative_path for item in kicks.items] == ["Drums/Kicks/kick.wav"]
    both = store.list_files(offset=0, limit=50, tags=["loop", "synth"])
    assert [item.relative_path for item in both.items] == ["Loops/Melodic/synth_lead.wav"]
    missing = store.list_files(offset=0, limit=50, tags=["kick", "loop"])
    assert not missing.items
    with pytest.raises(ValueError, match="invalid tag"):
        store.list_files(offset=0, limit=50, tags=["nope"])
    store.close()


def test_list_files_filters_by_key_and_bpm(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "c_major.wav")
    write_sine_wav(library / "c_minor.wav")
    write_sine_wav(library / "fs_minor.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store, form_estimator=lambda _path: FormEstimate(None, None))
    store.set_inferred("c_major.wav", bpm=80, key="C")
    store.set_inferred("c_minor.wav", bpm=128, key="Cm")
    store.set_inferred("fs_minor.wav", bpm=160, key="F#m")
    c_files = store.list_files(offset=0, limit=50, key="C")
    assert [item.relative_path for item in c_files.items] == ["c_major.wav", "c_minor.wav"]
    assert store.list_files(offset=0, limit=50, key="Cm").items[0].relative_path == "c_minor.wav"
    mid = store.list_files(offset=0, limit=50, bpm_min=110, bpm_max=130)
    assert [item.relative_path for item in mid.items] == ["c_minor.wav"]
    fast = store.list_files(offset=0, limit=50, bpm_min=150)
    assert [item.relative_path for item in fast.items] == ["fs_minor.wav"]
    both = store.list_files(offset=0, limit=50, key="C", bpm_min=70, bpm_max=90)
    assert [item.relative_path for item in both.items] == ["c_major.wav"]
    store.set_user("c_minor.wav", bpm=80)
    overridden = store.list_files(offset=0, limit=50, bpm_min=70, bpm_max=90)
    assert [item.relative_path for item in overridden.items] == ["c_major.wav", "c_minor.wav"]
    with pytest.raises(ValueError, match="invalid key"):
        store.list_files(offset=0, limit=50, key="Db")
    with pytest.raises(ValueError, match="invalid bpm"):
        store.list_files(offset=0, limit=50, bpm_min=130, bpm_max=110)
    store.close()


def test_list_files_filters_by_path_and_mtime(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "fresh.wav")
    write_sine_wav(library / "other.wav")
    write_sine_wav(library / "stale.wav")
    stale = library / "stale.wav"
    stale_mtime = time.time_ns() - 10 * 24 * 60 * 60 * 1_000_000_000
    os.utime(stale, ns=(stale.stat().st_atime_ns, stale_mtime))
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store, form_estimator=lambda _path: FormEstimate(None, None))
    by_path = store.list_files(offset=0, limit=50, paths=["fresh.wav", "missing.wav"])
    assert [item.relative_path for item in by_path.items] == ["fresh.wav"]
    empty = store.list_files(offset=0, limit=50, paths=[])
    assert empty.total == 0
    assert empty.items == []
    recent = store.list_files(
        offset=0, limit=50, mtime_after_ns=time.time_ns() - RECENT_WINDOW_NS
    )
    assert [item.relative_path for item in recent.items] == ["fresh.wav", "other.wav"]
    with pytest.raises(ValueError, match="invalid mtime_after"):
        store.list_files(offset=0, limit=50, mtime_after_ns=-1)
    store.close()


def test_list_files_matches_a_cached_path_tail(tmp_path: Path) -> None:
    library = tmp_path / "library"
    write_sine_wav(library / "Samples" / "Loops" / "lead.wav")
    write_sine_wav(library / "Samples" / "Drums" / "kick.wav")
    store = CatalogStore(tmp_path / "catalog.sqlite")
    store.initialize()
    scan_library(library, store, form_estimator=lambda _path: FormEstimate(None, None))
    tail = store.list_files(offset=0, limit=50, paths=["Loops/lead.wav"])
    assert [item.relative_path for item in tail.items] == ["Samples/Loops/lead.wav"]
    exact = store.list_files(offset=0, limit=50, paths=["Samples/Drums/kick.wav"])
    assert [item.relative_path for item in exact.items] == ["Samples/Drums/kick.wav"]
    store.close()
