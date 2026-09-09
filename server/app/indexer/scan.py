import os
from pathlib import Path

from app.catalog.paths import file_name, is_audio_file, parent_path, relative_posix
from app.catalog.store import CatalogStore, FileRecord
from app.indexer.audio import read_audio_info


def iter_audio_files(library_root: Path) -> list[Path]:
    audio_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(library_root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not name.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            path = Path(dirpath) / filename
            if is_audio_file(path):
                audio_files.append(path)
    return audio_files


def scan_library(library_root: Path, store: CatalogStore) -> int:
    records = [_record_for(library_root, path) for path in iter_audio_files(library_root)]
    return store.replace_all(records)


def _record_for(library_root: Path, path: Path) -> FileRecord:
    relative = relative_posix(library_root, path)
    stats = path.stat()
    audio = read_audio_info(path)
    return FileRecord(
        relative_path=relative,
        name=file_name(relative),
        parent_path=parent_path(relative),
        size_bytes=stats.st_size,
        mtime_ns=stats.st_mtime_ns,
        format=path.suffix.lower().lstrip("."),
        duration_seconds=audio.duration_seconds,
        sample_rate=audio.sample_rate,
        channels=audio.channels,
    )
