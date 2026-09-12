from dataclasses import asdict, dataclass

from sqlalchemy import ForeignKey, Index, func
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


class FileMeta(MappedAsDataclass, Base):
    __tablename__ = "file_meta"

    relative_path: Mapped[str] = mapped_column(
        ForeignKey("files.relative_path", ondelete="CASCADE"),
        primary_key=True,
    )
    bpm_inferred: Mapped[float | None] = mapped_column(default=None)
    bpm_user: Mapped[float | None] = mapped_column(default=None)
    key_inferred: Mapped[str | None] = mapped_column(default=None)
    key_user: Mapped[str | None] = mapped_column(default=None)
    audio_is_loop: Mapped[bool | None] = mapped_column(default=None)
    audio_bpm: Mapped[float | None] = mapped_column(default=None)

    def detached(self) -> "FileMeta":
        return FileMeta(**asdict(self))

    @property
    def bpm(self) -> float | None:
        return self.bpm_user if self.bpm_user is not None else self.bpm_inferred

    @property
    def key(self) -> str | None:
        return self.key_user if self.key_user is not None else self.key_inferred


Index("file_meta_bpm", func.coalesce(FileMeta.bpm_user, FileMeta.bpm_inferred))
Index("file_meta_key", func.coalesce(FileMeta.key_user, FileMeta.key_inferred))


class FileTagInferred(MappedAsDataclass, Base):
    __tablename__ = "file_tag_inferred"

    relative_path: Mapped[str] = mapped_column(
        ForeignKey("files.relative_path", ondelete="CASCADE"),
        primary_key=True,
    )
    slug: Mapped[str] = mapped_column(primary_key=True)
    facet: Mapped[str]
    source: Mapped[str]

    def detached(self) -> "FileTagInferred":
        return FileTagInferred(**asdict(self))


class FileTagUser(MappedAsDataclass, Base):
    __tablename__ = "file_tag_user"

    relative_path: Mapped[str] = mapped_column(
        ForeignKey("files.relative_path", ondelete="CASCADE"),
        primary_key=True,
    )
    slug: Mapped[str] = mapped_column(primary_key=True)
    facet: Mapped[str]
    present: Mapped[bool]

    def detached(self) -> "FileTagUser":
        return FileTagUser(**asdict(self))


class FileTag(MappedAsDataclass, Base):
    __tablename__ = "file_tag"

    relative_path: Mapped[str] = mapped_column(
        ForeignKey("files.relative_path", ondelete="CASCADE"),
        primary_key=True,
    )
    slug: Mapped[str] = mapped_column(primary_key=True)
    facet: Mapped[str]

    def detached(self) -> "FileTag":
        return FileTag(**asdict(self))


Index("file_tag_slug", FileTag.slug)


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
