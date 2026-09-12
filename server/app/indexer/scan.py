import os
import stat
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

from app.catalog.meta import plausible_bpm
from app.catalog.models import FileRecord
from app.catalog.paths import file_name, is_audio_file, parent_path
from app.catalog.store import CatalogStore
from app.catalog.tags import Inference, merge_inferred_tags
from app.indexer.audio import read_audio_info
from app.indexer.filename import parse_relative
from app.indexer.form import FormEstimate, estimate_form, should_estimate_form


def iter_audio_files(library_root: Path) -> Iterator[Path]:
    for dirpath, dirnames, filenames in os.walk(library_root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not name.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            path = Path(dirpath) / filename
            if is_audio_file(path):
                yield path


def scan_library(
    library_root: Path,
    store: CatalogStore,
    *,
    form_estimator: Callable[[Path], FormEstimate] = estimate_form,
    on_progress: Callable[[int, int], None] | None = None,
) -> int:
    progress = _reporter(on_progress)
    existing = store.fingerprints()
    progress(0, len(existing))
    seen, upserts, changed, indexed = _index_library(library_root, existing, progress)
    file_count = _commit_records(store, existing, seen, upserts)
    alive = {path for path in existing if path in seen}
    alive.update(record.relative_path for record in upserts)
    total = indexed + len(alive)
    progress(indexed, total)
    store.apply_inferences(
        _reporting(
            _inferences_for(library_root, store, alive, changed, form_estimator),
            indexed,
            total,
            progress,
        )
    )
    return file_count


def _reporter(on_progress: Callable[[int, int], None] | None) -> Callable[[int, int], None]:
    def report(done: int, total: int) -> None:
        if on_progress is not None:
            on_progress(done, total)

    return report


def _index_library(
    library_root: Path,
    existing: dict[str, tuple[int, int]],
    progress: Callable[[int, int], None],
) -> tuple[set[str], list[FileRecord], set[str], int]:
    seen: set[str] = set()
    upserts: list[FileRecord] = []
    changed: set[str] = set()
    indexed = 0
    known = len(existing)
    for path in iter_audio_files(library_root):
        indexed += 1
        if known > 0 and indexed <= known:
            progress(indexed, known)
        else:
            progress(indexed, 0)
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
        changed.add(relative)
    return seen, upserts, changed, indexed


def _commit_records(
    store: CatalogStore,
    existing: dict[str, tuple[int, int]],
    seen: set[str],
    upserts: list[FileRecord],
) -> int:
    delete_paths = [path for path in existing if path not in seen]
    if upserts or delete_paths:
        return store.apply_scan(upserts, delete_paths)
    return len(existing)


def _reporting(
    items: Iterable[Inference],
    start: int,
    total: int,
    report: Callable[[int, int], None],
) -> Iterator[Inference]:
    for offset, item in enumerate(items, start=1):
        yield item
        report(start + offset, total)


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


def _inferences_for(
    library_root: Path,
    store: CatalogStore,
    alive: set[str],
    changed: set[str],
    form_estimator: Callable[[Path], FormEstimate],
) -> Iterator[Inference]:
    stats = store.file_stats()
    audio_facts = store.audio_facts()
    for relative in sorted(alive):
        duration, fmt = stats.get(relative, (None, ""))
        if relative in changed:
            estimate = _estimate_changed(library_root / relative, fmt, duration, form_estimator)
            audio_is_loop, audio_bpm = estimate.is_loop, estimate.bpm
        else:
            audio_is_loop, audio_bpm = audio_facts.get(relative, (None, None))
        parsed = parse_relative(relative)
        bpm = parsed.bpm
        if bpm is None:
            bpm = _bpm_from_audio(audio_bpm)
        yield Inference(
            relative_path=relative,
            bpm=bpm,
            key=parsed.key,
            audio_is_loop=audio_is_loop,
            audio_bpm=audio_bpm,
            tags=merge_inferred_tags(
                path_tags=parsed.path_tags,
                filename_tags=parsed.filename_tags,
                duration_seconds=duration,
                audio_is_loop=audio_is_loop,
            ),
        )


def _estimate_changed(
    path: Path,
    fmt: str,
    duration: float | None,
    form_estimator: Callable[[Path], FormEstimate],
) -> FormEstimate:
    if not should_estimate_form(fmt, duration):
        return FormEstimate(None, None)
    return form_estimator(path)


def _bpm_from_audio(audio_bpm: float | None) -> float | None:
    if audio_bpm is None:
        return None
    if not plausible_bpm(round(audio_bpm), tagged=False):
        return None
    return audio_bpm
