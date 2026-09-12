import re

KEY_ROOTS = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
CANONICAL_KEYS = frozenset((*KEY_ROOTS, *(f"{root}m" for root in KEY_ROOTS)))
MAX_BPM = 400.0
MIN_INFERRED_BPM = 65
MAX_INFERRED_BPM = 240
_DRUM_MACHINE_NUMBERS = frozenset({101, 202, 303, 404, 505, 606, 707, 808, 909})

_FLAT_TO_SHARP = {
    "CB": "B",
    "DB": "C#",
    "EB": "D#",
    "FB": "E",
    "GB": "F#",
    "AB": "G#",
    "BB": "A#",
}
_SHARP_TO_CANONICAL = {
    "C#": "C#",
    "D#": "D#",
    "E#": "F",
    "F#": "F#",
    "G#": "G#",
    "A#": "A#",
    "B#": "C",
}
_KEY_TOKEN = re.compile(
    r"(?i)^([A-G])([#♯b♭])?(?:[ ]*(major|minor|maj|min|m))?$"
)


def check_bpm(bpm: float | None) -> None:
    if bpm is None:
        return
    if not 0 < bpm <= MAX_BPM:
        raise ValueError("invalid bpm")


def check_key(key: str | None) -> None:
    if key is None:
        return
    if key not in CANONICAL_KEYS:
        raise ValueError("invalid key")


BPM_RANGES: dict[str, tuple[float, float | None]] = {
    "70-90": (70.0, 90.0),
    "90-110": (90.0, 110.0),
    "110-130": (110.0, 130.0),
    "130-150": (130.0, 150.0),
    "150+": (150.0, None),
}


def key_filter_values(key: str) -> tuple[str, ...]:
    if key in KEY_ROOTS:
        return (key, f"{key}m")
    if key in CANONICAL_KEYS:
        return (key,)
    raise ValueError("invalid key")


def parse_bpm_range(token: str) -> tuple[float, float | None]:
    bounds = BPM_RANGES.get(token)
    if bounds is None:
        raise ValueError("invalid bpm")
    return bounds


def plausible_bpm(value: int, *, tagged: bool) -> bool:
    if not MIN_INFERRED_BPM <= value <= MAX_INFERRED_BPM:
        return False
    if tagged:
        return True
    return value not in _DRUM_MACHINE_NUMBERS


def canonical_key(token: str) -> str | None:
    matched = _KEY_TOKEN.fullmatch(token.strip())
    if matched is None:
        return None
    letter, accidental, mode = matched.group(1, 2, 3)
    root = _canonical_root(letter.upper(), accidental)
    if root is None:
        return None
    minor = mode is not None and mode.lower() in {"m", "min", "minor"}
    key = f"{root}m" if minor else root
    if key not in CANONICAL_KEYS:
        return None
    return key


def _canonical_root(letter: str, accidental: str | None) -> str | None:
    if accidental is None:
        return letter
    if accidental in {"b", "♭"}:
        return _FLAT_TO_SHARP.get(f"{letter}B")
    return _SHARP_TO_CANONICAL.get(f"{letter}#")
