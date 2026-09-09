from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from sqlite3 import Connection
from threading import Lock

from sqlalchemy import create_engine, delete, event, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.catalog.listing import child_folder_names
from app.catalog.models import Base, CatalogListing, FileRecord, FolderEntry


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

    def replace_all(self, records: list[FileRecord]) -> int:
        with self._session() as session:
            session.execute(delete(FileRecord))
            session.add_all(record.detached() for record in records)
            session.commit()
        return len(records)

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

    def close(self) -> None:
        with self._lock:
            self._engine.dispose()


def _parents_under(folder: str) -> ColumnElement[bool]:
    if not folder:
        return FileRecord.parent_path != ""
    return FileRecord.parent_path.startswith(f"{folder}/", autoescape=True)


def _configure_sqlite(dbapi_connection: Connection, _connection_record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
