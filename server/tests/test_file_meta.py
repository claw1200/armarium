import sqlite3
from pathlib import Path

import pytest

from app.catalog.meta import CANONICAL_KEYS, check_bpm, check_key
from app.catalog.store import CatalogStore
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
