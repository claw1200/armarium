import os
import stat
from collections.abc import Iterator
from pathlib import Path

from app.catalog.models import FileRecord
from app.catalog.paths import file_name, is_audio_file, parent_path
from app.catalog.store import CatalogStore
from app.indexer.audio import read_audio_info


def iter_audio_files(library_root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(library_root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not name.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            path = Path(dirpath) / filename
            if is_audio_file(path):
                yield path


def scan_library(library_root: Path, store: CatalogStore) -> int:
    existing = store.fingerprints()
    seen: set[str] = set()
    upserts: list[FileRecord] = []
    for path in iter_audio_files(library_root):
        try:
            stats = path.stat(follow_symlinks=False)
        except OSError:
            continue
        if not stat.S_ISREG(stats.st_mode):
            continue
        try:
            relative = path.relative_to(library_root).as_posix()
        except ValueError:
            continue
        seen.add(relative)
        if existing.get(relative) == (stats.st_size, stats.st_mtime_ns):
            continue
        try:
            upserts.append(_record_for(path, relative, stats))
        except (OSError, ValueError):
            continue
    delete_paths = [path for path in existing if path not in seen]
    if not upserts and not delete_paths:
        return len(existing)
    return store.apply_scan(upserts, delete_paths)


def _record_for(path: Path, relative: str, stats: os.stat_result) -> FileRecord:
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
