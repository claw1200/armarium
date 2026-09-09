from dataclasses import asdict, dataclass

from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class Base(DeclarativeBase):
    pass


class FileRecord(MappedAsDataclass, Base):
    __tablename__ = "files"

    relative_path: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    parent_path: Mapped[str] = mapped_column(index=True)
    size_bytes: Mapped[int]
    mtime_ns: Mapped[int]
    format: Mapped[str]
    duration_seconds: Mapped[float | None] = mapped_column(default=None)
    sample_rate: Mapped[int | None] = mapped_column(default=None)
    channels: Mapped[int | None] = mapped_column(default=None)

    def detached(self) -> "FileRecord":
        return FileRecord(**asdict(self))


@dataclass(frozen=True, slots=True)
class FolderEntry:
    name: str
    path: str


@dataclass(frozen=True, slots=True)
class CatalogListing:
    path: str
    folders: list[FolderEntry]
    files: list[FileRecord]


@dataclass(frozen=True, slots=True)
class FilePage:
    items: list[FileRecord]
    total: int
    limit: int
    offset: int
