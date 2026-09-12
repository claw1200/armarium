from collections.abc import Collection, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from sqlite3 import Connection
from threading import Lock
from types import EllipsisType

from sqlalchemy import create_engine, delete, event, func, or_, select, text, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import count

from app.catalog.listing import child_folder_names
from app.catalog.meta import check_bpm, check_key, key_filter_values
from app.catalog.models import (
    Base,
    CatalogListing,
    FileMeta,
    FilePage,
    FileRecord,
    FileTag,
    FileTagInferred,
    FileTagUser,
    FolderEntry,
)
from app.catalog.tags import (
    FORM_SLUGS,
    Inference,
    check_tag,
    facet_for,
    ordered_slugs,
)

FILE_SORTS = frozenset({"path", "name", "duration"})
RECENT_WINDOW_NS = 7 * 24 * 60 * 60 * 1_000_000_000
_SQLITE_IN_CHUNK = 500
_SORT_COLUMNS = {
    "path": (FileRecord.relative_path,),
    "name": (FileRecord.name, FileRecord.relative_path),
    "duration": (FileRecord.duration_seconds, FileRecord.relative_path),
}


class CatalogStore:
    def __init__(self, database_path: Path) -> None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._engine = create_engine(
            f"sqlite:///{database_path.resolve()}",
            connect_args={"check_same_thread": False},
        )
        event.listen(self._engine, "connect", _configure_sqlite)

    @contextmanager
    def _session(self) -> Iterator[Session]:
        with self._lock, Session(self._engine) as session:
            yield session

    def initialize(self) -> None:
        Base.metadata.create_all(self._engine)
        with self._session() as session:
            _ensure_file_meta_columns(session)
            session.commit()

    def fingerprints(self) -> dict[str, tuple[int, int]]:
        with self._session() as session:
            rows = session.execute(
                select(FileRecord.relative_path, FileRecord.size_bytes, FileRecord.mtime_ns)
            )
            return {relative: (size, mtime) for relative, size, mtime in rows}

    def file_stats(self) -> dict[str, tuple[float | None, str]]:
        with self._session() as session:
            rows = session.execute(
                select(FileRecord.relative_path, FileRecord.duration_seconds, FileRecord.format)
            )
            return {relative: (duration, fmt) for relative, duration, fmt in rows}

    def audio_facts(self) -> dict[str, tuple[bool | None, float | None]]:
        with self._session() as session:
            rows = session.execute(
                select(FileMeta.relative_path, FileMeta.audio_is_loop, FileMeta.audio_bpm)
            )
            return {relative: (is_loop, bpm) for relative, is_loop, bpm in rows}

    def apply_scan(self, upserts: Sequence[FileRecord], delete_paths: Collection[str]) -> int:
        with self._session() as session:
            _delete_paths(session, delete_paths)
            _upsert_records(session, upserts)
            session.commit()
            return session.scalar(select(count()).select_from(FileRecord)) or 0

    def get(self, relative_path: str) -> FileRecord | None:
        with self._session() as session:
            record = session.get(FileRecord, relative_path)
            return record.detached() if record is not None else None

    def get_meta(self, relative_path: str) -> FileMeta | None:
        with self._session() as session:
            meta = session.get(FileMeta, relative_path)
            return meta.detached() if meta is not None else None

    def set_inferred(
        self,
        relative_path: str,
        *,
        bpm: float | None | EllipsisType = ...,
        key: str | None | EllipsisType = ...,
    ) -> FileMeta:
        return self._write_meta(
            relative_path,
            bpm_inferred=_checked_bpm(bpm),
            key_inferred=_checked_key(key),
        )

    def set_user(
        self,
        relative_path: str,
        *,
        bpm: float | None | EllipsisType = ...,
        key: str | None | EllipsisType = ...,
    ) -> FileMeta:
        return self._write_meta(
            relative_path,
            bpm_user=_checked_bpm(bpm),
            key_user=_checked_key(key),
        )

    def set_user_tag(self, relative_path: str, slug: str, *, present: bool) -> None:
        check_tag(slug)
        with self._session() as session:
            if session.get(FileRecord, relative_path) is None:
                raise LookupError(relative_path)
            statement = sqlite_insert(FileTagUser).values(
                relative_path=relative_path,
                slug=slug,
                facet=facet_for(slug),
                present=present,
            )
            statement = statement.on_conflict_do_update(
                index_elements=[FileTagUser.relative_path, FileTagUser.slug],
                set_={
                    "facet": statement.excluded.facet,
                    "present": statement.excluded.present,
                },
            )
            session.execute(statement)
            _refresh_effective(session, [relative_path])
            session.commit()

    def list_folder(self, folder: str) -> CatalogListing:
        with self._session() as session:
            files = [
                row.detached()
                for row in session.scalars(
                    select(FileRecord)
                    .where(FileRecord.parent_path == folder)
                    .order_by(FileRecord.name)
                )
            ]
            parent_paths = list(
                session.scalars(
                    select(FileRecord.parent_path).where(_parents_under(folder)).distinct()
                )
            )
        folder_names = child_folder_names(parent_paths, folder)
        folders = [
            FolderEntry(name=name, path=f"{folder}/{name}" if folder else name)
            for name in folder_names
        ]
        return CatalogListing(path=folder, folders=folders, files=files)

    def list_files(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        offset: int,
        limit: int,
        prefix: str = "",
        query: str = "",
        sort: str = "path",
        tags: Sequence[str] = (),
        key: str | None = None,
        bpm_min: float | None = None,
        bpm_max: float | None = None,
        paths: Sequence[str] | None = None,
        mtime_after_ns: int | None = None,
    ) -> FilePage:
        order = _SORT_COLUMNS.get(sort)
        if order is None:
            raise ValueError("invalid sort")
        wanted = _wanted_paths(paths)
        if paths is not None and not wanted:
            return FilePage(items=[], total=0, limit=limit, offset=offset)
        filters = _file_filters(
            prefix, query, tags, key, bpm_min, bpm_max, wanted, mtime_after_ns
        )
        listing = select(FileRecord)
        counted = select(count()).select_from(FileRecord)
        if key is not None or bpm_min is not None or bpm_max is not None:
            listing = listing.join(FileMeta)
            counted = counted.join(FileMeta)
        with self._session() as session:
            total = session.scalar(counted.where(*filters)) or 0
            items = [
                row.detached()
                for row in session.scalars(
                    listing.where(*filters).order_by(*order).offset(offset).limit(limit)
                )
            ]
        return FilePage(items=items, total=total, limit=limit, offset=offset)

    def meta_by_paths(self, paths: Sequence[str]) -> dict[str, FileMeta]:
        unique = list(dict.fromkeys(paths))
        found: dict[str, FileMeta] = {}
        with self._session() as session:
            for offset in range(0, len(unique), _SQLITE_IN_CHUNK):
                chunk = unique[offset : offset + _SQLITE_IN_CHUNK]
                for row in session.scalars(
                    select(FileMeta).where(FileMeta.relative_path.in_(chunk))
                ):
                    found[row.relative_path] = row.detached()
        return found

    def tags_by_paths(self, paths: Sequence[str]) -> dict[str, list[str]]:
        unique = list(dict.fromkeys(paths))
        found: dict[str, list[str]] = {path: [] for path in unique}
        with self._session() as session:
            for offset in range(0, len(unique), _SQLITE_IN_CHUNK):
                chunk = unique[offset : offset + _SQLITE_IN_CHUNK]
                grouped: dict[str, list[tuple[str, str]]] = {}
                for row in session.scalars(select(FileTag).where(FileTag.relative_path.in_(chunk))):
                    grouped.setdefault(row.relative_path, []).append((row.slug, row.facet))
                for path, pairs in grouped.items():
                    found[path] = ordered_slugs(slug for slug, _facet in pairs)
        return found

    def close(self) -> None:
        with self._lock:
            self._engine.dispose()

    def _write_meta(
        self, relative_path: str, **columns: float | str | bool | None | EllipsisType
    ) -> FileMeta:
        values = {name: value for name, value in columns.items() if value is not ...}
        if not values:
            raise TypeError("bpm or key is required")
        with self._session() as session:
            if session.get(FileRecord, relative_path) is None:
                raise LookupError(relative_path)
            statement = sqlite_insert(FileMeta).values(relative_path=relative_path, **values)
            statement = statement.on_conflict_do_update(
                index_elements=[FileMeta.relative_path],
                set_={name: getattr(statement.excluded, name) for name in values},
            )
            session.execute(statement)
            meta = session.get(FileMeta, relative_path)
            if meta is None:
                raise LookupError(relative_path)
            result = meta.detached()
            session.commit()
            return result

    def apply_inferences(self, updates: Iterable[Inference]) -> None:
        rows = list(updates)
        if not rows:
            return
        upserts: list[dict[str, str | float | bool | None]] = []
        clears: list[str] = []
        for item in rows:
            check_bpm(item.bpm)
            check_key(item.key)
            check_bpm(item.audio_bpm)
            if (
                item.bpm is None
                and item.key is None
                and item.audio_is_loop is None
                and item.audio_bpm is None
            ):
                clears.append(item.relative_path)
            else:
                upserts.append(
                    {
                        "relative_path": item.relative_path,
                        "bpm_inferred": item.bpm,
                        "key_inferred": item.key,
                        "audio_is_loop": item.audio_is_loop,
                        "audio_bpm": item.audio_bpm,
                    }
                )
        paths = [item.relative_path for item in rows]
        with self._session() as session:
            _clear_inferred(session, clears)
            _upsert_inferred(session, upserts)
            _replace_inferred_tags(session, rows)
            _refresh_effective(session, paths)
            session.commit()


def _delete_paths(session: Session, delete_paths: Collection[str]) -> None:
    paths = list(delete_paths)
    for offset in range(0, len(paths), _SQLITE_IN_CHUNK):
        chunk = paths[offset : offset + _SQLITE_IN_CHUNK]
        session.execute(delete(FileRecord).where(FileRecord.relative_path.in_(chunk)))


def _upsert_records(session: Session, upserts: Sequence[FileRecord]) -> None:
    if not upserts:
        return
    statement = sqlite_insert(FileRecord)
    statement = statement.on_conflict_do_update(
        index_elements=[FileRecord.relative_path],
        set_={
            column.name: getattr(statement.excluded, column.name)
            for column in FileRecord.__table__.columns
            if column.name != "relative_path"
        },
    )
    payload = [asdict(record.detached()) for record in upserts]
    for offset in range(0, len(payload), _SQLITE_IN_CHUNK):
        session.execute(statement, payload[offset : offset + _SQLITE_IN_CHUNK])


def _upsert_inferred(
    session: Session, upserts: Sequence[dict[str, str | float | bool | None]]
) -> None:
    if not upserts:
        return
    statement = sqlite_insert(FileMeta)
    statement = statement.on_conflict_do_update(
        index_elements=[FileMeta.relative_path],
        set_={
            "bpm_inferred": statement.excluded.bpm_inferred,
            "key_inferred": statement.excluded.key_inferred,
            "audio_is_loop": statement.excluded.audio_is_loop,
            "audio_bpm": statement.excluded.audio_bpm,
        },
    )
    for offset in range(0, len(upserts), _SQLITE_IN_CHUNK):
        session.execute(statement, upserts[offset : offset + _SQLITE_IN_CHUNK])


def _clear_inferred(session: Session, paths: Sequence[str]) -> None:
    for offset in range(0, len(paths), _SQLITE_IN_CHUNK):
        chunk = paths[offset : offset + _SQLITE_IN_CHUNK]
        session.execute(
            update(FileMeta)
            .where(FileMeta.relative_path.in_(chunk))
            .values(bpm_inferred=None, key_inferred=None, audio_is_loop=None, audio_bpm=None)
        )


def _replace_inferred_tags(session: Session, updates: Sequence[Inference]) -> None:
    paths = [item.relative_path for item in updates]
    for offset in range(0, len(paths), _SQLITE_IN_CHUNK):
        chunk = paths[offset : offset + _SQLITE_IN_CHUNK]
        session.execute(delete(FileTagInferred).where(FileTagInferred.relative_path.in_(chunk)))
    payload = [
        {
            "relative_path": item.relative_path,
            "slug": hit.slug,
            "facet": hit.facet,
            "source": hit.source,
        }
        for item in updates
        for hit in item.tags
    ]
    if not payload:
        return
    statement = sqlite_insert(FileTagInferred)
    for offset in range(0, len(payload), _SQLITE_IN_CHUNK):
        session.execute(statement, payload[offset : offset + _SQLITE_IN_CHUNK])


def _refresh_effective(session: Session, paths: Sequence[str]) -> None:
    unique = list(dict.fromkeys(paths))
    for offset in range(0, len(unique), _SQLITE_IN_CHUNK):
        chunk = unique[offset : offset + _SQLITE_IN_CHUNK]
        inferred_by_path: dict[str, list[FileTagInferred]] = {path: [] for path in chunk}
        user_by_path: dict[str, list[FileTagUser]] = {path: [] for path in chunk}
        for row in session.scalars(
            select(FileTagInferred).where(FileTagInferred.relative_path.in_(chunk))
        ):
            inferred_by_path[row.relative_path].append(row)
        for row in session.scalars(
            select(FileTagUser).where(FileTagUser.relative_path.in_(chunk))
        ):
            user_by_path[row.relative_path].append(row)
        session.execute(delete(FileTag).where(FileTag.relative_path.in_(chunk)))
        payload = []
        for path in chunk:
            for slug, facet in _effective_pairs(inferred_by_path[path], user_by_path[path]):
                payload.append({"relative_path": path, "slug": slug, "facet": facet})
        if payload:
            session.execute(sqlite_insert(FileTag), payload)


def _effective_pairs(
    inferred: Sequence[FileTagInferred],
    user: Sequence[FileTagUser],
) -> list[tuple[str, str]]:
    slugs = {row.slug: row.facet for row in inferred}
    user_forms: list[str] = []
    for row in user:
        if row.present:
            slugs[row.slug] = row.facet
            if row.slug in FORM_SLUGS:
                user_forms.append(row.slug)
        else:
            slugs.pop(row.slug, None)
    forms = [slug for slug in slugs if slug in FORM_SLUGS]
    if len(forms) > 1:
        keep = user_forms[-1] if user_forms else forms[0]
        for slug in forms:
            if slug != keep:
                del slugs[slug]
    return [(slug, slugs[slug]) for slug in ordered_slugs(slugs)]


def _ensure_file_meta_columns(session: Session) -> None:
    rows = session.execute(text("PRAGMA table_info(file_meta)")).fetchall()
    columns = {row[1] for row in rows}
    if "audio_is_loop" not in columns:
        session.execute(text("ALTER TABLE file_meta ADD COLUMN audio_is_loop BOOLEAN"))
    if "audio_bpm" not in columns:
        session.execute(text("ALTER TABLE file_meta ADD COLUMN audio_bpm FLOAT"))


def _checked_bpm(bpm: float | None | EllipsisType) -> float | None | EllipsisType:
    if bpm is ...:
        return ...
    check_bpm(bpm)
    return bpm


def _checked_key(key: str | None | EllipsisType) -> str | None | EllipsisType:
    if key is ...:
        return ...
    check_key(key)
    return key


def _parents_under(folder: str) -> ColumnElement[bool]:
    if not folder:
        return FileRecord.parent_path != ""
    return FileRecord.parent_path.startswith(f"{folder}/", autoescape=True)


def _files_under(prefix: str) -> ColumnElement[bool]:
    return or_(
        FileRecord.parent_path == prefix,
        FileRecord.parent_path.startswith(f"{prefix}/", autoescape=True),
    )


def _path_matches(query: str) -> ColumnElement[bool]:
    return FileRecord.relative_path.contains(query, autoescape=True)


def _wanted_paths(paths: Sequence[str] | None) -> tuple[str, ...]:
    if paths is None:
        return ()
    return tuple(dict.fromkeys(path for path in paths if path))


def _paths_in(paths: Sequence[str]) -> ColumnElement[bool]:
    clauses = [
        FileRecord.relative_path.in_(paths[offset : offset + _SQLITE_IN_CHUNK])
        for offset in range(0, len(paths), _SQLITE_IN_CHUNK)
    ]
    clauses.extend(
        FileRecord.relative_path.endswith(f"/{path}", autoescape=True) for path in paths
    )
    return or_(*clauses)


def _file_filters(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    prefix: str,
    query: str,
    tags: Sequence[str],
    key: str | None,
    bpm_min: float | None,
    bpm_max: float | None,
    paths: Sequence[str],
    mtime_after_ns: int | None,
) -> tuple[ColumnElement[bool], ...]:
    if bpm_min is not None and bpm_max is not None and bpm_min >= bpm_max:
        raise ValueError("invalid bpm")
    if mtime_after_ns is not None and mtime_after_ns < 0:
        raise ValueError("invalid mtime_after")
    filters: tuple[ColumnElement[bool], ...] = ()
    if prefix:
        filters += (_files_under(prefix),)
    if query:
        filters += (_path_matches(query),)
    if paths:
        filters += (_paths_in(paths),)
    if mtime_after_ns is not None:
        filters += (FileRecord.mtime_ns >= mtime_after_ns,)
    for slug in dict.fromkeys(tags):
        check_tag(slug)
        filters += (_has_tag(slug),)
    if key is not None:
        filters += (
            func.coalesce(FileMeta.key_user, FileMeta.key_inferred).in_(
                key_filter_values(key)
            ),
        )
    if bpm_min is not None:
        check_bpm(bpm_min)
        filters += (func.coalesce(FileMeta.bpm_user, FileMeta.bpm_inferred) >= bpm_min,)
    if bpm_max is not None:
        check_bpm(bpm_max)
        filters += (func.coalesce(FileMeta.bpm_user, FileMeta.bpm_inferred) < bpm_max,)
    return filters


def _has_tag(slug: str) -> ColumnElement[bool]:
    return FileRecord.relative_path.in_(select(FileTag.relative_path).where(FileTag.slug == slug))


def _configure_sqlite(dbapi_connection: Connection, _connection_record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
