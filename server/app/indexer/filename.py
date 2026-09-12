import re
from dataclasses import dataclass
from pathlib import Path

from app.catalog.meta import canonical_key, plausible_bpm
from app.catalog.paths import file_name, parent_path
from app.catalog.tags import TagHit, match_tags

_DELIM = r"[ _()-]"
_BPM = re.compile(
    rf"(?:^|{_DELIM})(\d{{2,3}})({_DELIM}*bpm)?(?={_DELIM}|$)",
    re.IGNORECASE,
)
_KEY = re.compile(
    rf"(?:^|{_DELIM})([A-G][#♯b♭]?(?:[ ]*(?:major|minor|maj|min|m))?)(?={_DELIM}|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FilenameMeta:
    bpm: float | None
    key: str | None
    filename_tags: tuple[TagHit, ...]
    path_tags: tuple[TagHit, ...]


def parse_filename(name: str) -> FilenameMeta:
    return parse_relative(name)


def parse_relative(relative: str) -> FilenameMeta:
    name = file_name(relative)
    stem = Path(name).stem
    parent = parent_path(relative)
    return FilenameMeta(
        bpm=_parse_bpm(stem),
        key=_parse_key(stem),
        filename_tags=match_tags(stem, "filename"),
        path_tags=match_tags(parent, "path") if parent else (),
    )


def _parse_bpm(stem: str) -> float | None:
    tagged: list[int] = []
    bare: list[int] = []
    for match in _BPM.finditer(stem):
        value = int(match.group(1))
        if match.group(2) is not None:
            tagged.append(value)
        else:
            bare.append(value)
    for value in tagged:
        if plausible_bpm(value, tagged=True):
            return float(value)
    for value in bare:
        if plausible_bpm(value, tagged=False):
            return float(value)
    return None


def _parse_key(stem: str) -> str | None:
    for match in _KEY.finditer(stem):
        key = canonical_key(match.group(1))
        if key is not None:
            return key
    return None
