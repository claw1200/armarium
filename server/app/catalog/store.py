from collections.abc import Collection, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from sqlite3 import Connection
from threading import Lock

from sqlalchemy import create_engine, delete, event, or_, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.functions import count

from app.catalog.listing import child_folder_names
from app.catalog.models import Base, CatalogListing, FilePage, FileRecord, FolderEntry

FILE_SORTS = frozenset({"path", "name", "duration"})
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

    def fingerprints(self) -> dict[str, tuple[int, int]]:
        with self._session() as session:
            rows = session.execute(
                select(FileRecord.relative_path, FileRecord.size_bytes, FileRecord.mtime_ns)
            )
            return {relative: (size, mtime) for relative, size, mtime in rows}

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

    def list_files(
        self,
        *,
        offset: int,
        limit: int,
        prefix: str = "",
        sort: str = "path",
    ) -> FilePage:
        order = _SORT_COLUMNS.get(sort)
        if order is None:
            raise ValueError("invalid sort")
        filters = (_files_under(prefix),) if prefix else ()
        with self._session() as session:
            total = (
                session.scalar(select(count()).select_from(FileRecord).where(*filters)) or 0
            )
            items = [
                row.detached()
                for row in session.scalars(
                    select(FileRecord).where(*filters).order_by(*order).offset(offset).limit(limit)
                )
            ]
        return FilePage(items=items, total=total, limit=limit, offset=offset)

    def close(self) -> None:
        with self._lock:
            self._engine.dispose()


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


def _parents_under(folder: str) -> ColumnElement[bool]:
    if not folder:
        return FileRecord.parent_path != ""
    return FileRecord.parent_path.startswith(f"{folder}/", autoescape=True)


def _files_under(prefix: str) -> ColumnElement[bool]:
    return or_(
        FileRecord.parent_path == prefix,
        FileRecord.parent_path.startswith(f"{prefix}/", autoescape=True),
    )


def _configure_sqlite(dbapi_connection: Connection, _connection_record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
