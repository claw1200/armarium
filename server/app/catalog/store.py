from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.catalog.listing import child_folder_names


@dataclass(frozen=True, slots=True)
class FileRecord:
    relative_path: str
    name: str
    parent_path: str
    size_bytes: int
    mtime_ns: int
    format: str
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None


@dataclass(frozen=True, slots=True)
class FolderEntry:
    name: str
    path: str


@dataclass(frozen=True, slots=True)
class CatalogListing:
    path: str
    folders: list[FolderEntry]
    files: list[FileRecord]


class CatalogStore:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(self._database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")

    def initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                relative_path TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                parent_path TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                format TEXT NOT NULL,
                duration_seconds REAL,
                sample_rate INTEGER,
                channels INTEGER
            )
            """
        )
        self._connection.execute(
            "CREATE INDEX IF NOT EXISTS files_parent_path ON files (parent_path)"
        )
        self._connection.commit()

    def replace_all(self, records: list[FileRecord]) -> int:
        with self._connection:
            self._connection.execute("DELETE FROM files")
            self._connection.executemany(
                """
                INSERT INTO files (
                    relative_path, name, parent_path, size_bytes, mtime_ns,
                    format, duration_seconds, sample_rate, channels
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.relative_path,
                        record.name,
                        record.parent_path,
                        record.size_bytes,
                        record.mtime_ns,
                        record.format,
                        record.duration_seconds,
                        record.sample_rate,
                        record.channels,
                    )
                    for record in records
                ],
            )
        return len(records)

    def list_folder(self, folder: str) -> CatalogListing:
        files = [
            self._record_from_row(row)
            for row in self._connection.execute(
                """
                SELECT relative_path, name, parent_path, size_bytes, mtime_ns,
                       format, duration_seconds, sample_rate, channels
                FROM files
                WHERE parent_path = ?
                ORDER BY name
                """,
                (folder,),
            )
        ]
        parent_rows = self._connection.execute(
            "SELECT DISTINCT parent_path FROM files WHERE parent_path != ''"
        )
        folder_names = child_folder_names([row["parent_path"] for row in parent_rows], folder)
        folders = [
            FolderEntry(name=name, path=f"{folder}/{name}" if folder else name)
            for name in folder_names
        ]
        return CatalogListing(path=folder, folders=folders, files=files)

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> FileRecord:
        return FileRecord(
            relative_path=row["relative_path"],
            name=row["name"],
            parent_path=row["parent_path"],
            size_bytes=row["size_bytes"],
            mtime_ns=row["mtime_ns"],
            format=row["format"],
            duration_seconds=row["duration_seconds"],
            sample_rate=row["sample_rate"],
            channels=row["channels"],
        )

    def close(self) -> None:
        self._connection.close()
