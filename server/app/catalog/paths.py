from pathlib import Path

AUDIO_SUFFIXES = frozenset(
    {".aif", ".aiff", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".wave"}
)
AUDIO_MEDIA_TYPES = {
    "aif": "audio/aiff",
    "aiff": "audio/aiff",
    "flac": "audio/flac",
    "m4a": "audio/mp4",
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "wav": "audio/wav",
    "wave": "audio/wav",
}


def parse_folder_path(raw: str | None) -> str:
    if raw is None or raw in {"", "/"}:
        return ""
    parts = [part for part in raw.replace("\\", "/").strip("/").split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError("path must stay inside the library")
    return "/".join(parts)


def parse_file_path(raw: str | None) -> str:
    relative = parse_folder_path(raw)
    if not relative:
        raise ValueError("path must stay inside the library")
    return relative


def media_type_for(format_name: str) -> str:
    return AUDIO_MEDIA_TYPES.get(format_name.lower(), "application/octet-stream")


def audio_disk_path(library_root: Path, relative: str) -> Path | None:
    if not relative:
        return None
    root = library_root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return path


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
