from pathlib import Path

AUDIO_SUFFIXES = frozenset(
    {".aif", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".wave"}
)


def parse_folder_path(raw: str | None) -> str:
    if raw is None or raw in {"", "/"}:
        return ""
    parts = [part for part in raw.replace("\\", "/").strip("/").split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError("path must stay inside the library")
    return "/".join(parts)


def relative_posix(library_root: Path, path: Path) -> str:
    return path.resolve().relative_to(library_root.resolve()).as_posix()


def parent_path(relative_posix_path: str) -> str:
    if "/" not in relative_posix_path:
        return ""
    return relative_posix_path.rsplit("/", 1)[0]


def file_name(relative_posix_path: str) -> str:
    return relative_posix_path.rsplit("/", 1)[-1]


def is_audio_file(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_SUFFIXES
