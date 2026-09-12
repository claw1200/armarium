from collections.abc import Iterable, Sequence
from dataclasses import dataclass

FACET_FORM = "form"
FACET_ROLE = "role"
FACET_FUNCTION = "function"
FACET_ORDER = (FACET_FORM, FACET_ROLE, FACET_FUNCTION)
FORM_SLUGS = frozenset({"loop", "one-shot"})
SOURCE_PATH = "path"
SOURCE_FILENAME = "filename"
SOURCE_DURATION = "duration"
SOURCE_ESTIMATOR = "estimator"
ONE_SHOT_MAX_SECONDS = 0.6
ESTIMATOR_MAX_SECONDS = 60.0
ESTIMATOR_FORMATS = frozenset({"wav", "wave", "aif", "aiff"})

SLUG_FACET = {
    "loop": FACET_FORM,
    "one-shot": FACET_FORM,
    "kick": FACET_ROLE,
    "snare": FACET_ROLE,
    "clap": FACET_ROLE,
    "hat": FACET_ROLE,
    "ride": FACET_ROLE,
    "crash": FACET_ROLE,
    "tom": FACET_ROLE,
    "perc": FACET_ROLE,
    "bass": FACET_ROLE,
    "synth": FACET_ROLE,
    "pad": FACET_ROLE,
    "keys": FACET_ROLE,
    "guitar": FACET_ROLE,
    "vocal": FACET_ROLE,
    "fx": FACET_ROLE,
    "melody": FACET_FUNCTION,
    "chord": FACET_FUNCTION,
    "arp": FACET_FUNCTION,
    "rhythm": FACET_FUNCTION,
    "texture": FACET_FUNCTION,
    "riser": FACET_FUNCTION,
    "impact": FACET_FUNCTION,
    "sweep": FACET_FUNCTION,
}
CANONICAL_TAGS = frozenset(SLUG_FACET)

_ALIAS_SLUG = {
    "loop": "loop",
    "loops": "loop",
    "lp": "loop",
    "looping": "loop",
    "one shot": "one-shot",
    "oneshot": "one-shot",
    "one-shot": "one-shot",
    "one shots": "one-shot",
    "oneshots": "one-shot",
    "one-shots": "one-shot",
    "os": "one-shot",
    "kick": "kick",
    "kicks": "kick",
    "bd": "kick",
    "bassdrum": "kick",
    "bass drum": "kick",
    "kickdrum": "kick",
    "kick drum": "kick",
    "snare": "snare",
    "snares": "snare",
    "sd": "snare",
    "clap": "clap",
    "claps": "clap",
    "clp": "clap",
    "hat": "hat",
    "hats": "hat",
    "hh": "hat",
    "hihat": "hat",
    "hihats": "hat",
    "hi hat": "hat",
    "hi-hat": "hat",
    "oh": "hat",
    "ch": "hat",
    "openhat": "hat",
    "open hat": "hat",
    "open-hat": "hat",
    "closedhat": "hat",
    "closed hat": "hat",
    "closed-hat": "hat",
    "ride": "ride",
    "rides": "ride",
    "crash": "crash",
    "crashes": "crash",
    "tom": "tom",
    "toms": "tom",
    "perc": "perc",
    "percs": "perc",
    "percussion": "perc",
    "bass": "bass",
    "basses": "bass",
    "sub": "bass",
    "subbass": "bass",
    "sub bass": "bass",
    "synth": "synth",
    "synths": "synth",
    "syn": "synth",
    "synthesizer": "synth",
    "pad": "pad",
    "pads": "pad",
    "keys": "keys",
    "keyboards": "keys",
    "keyboard": "keys",
    "guitar": "guitar",
    "guitars": "guitar",
    "gtr": "guitar",
    "vocal": "vocal",
    "vocals": "vocal",
    "vox": "vocal",
    "voice": "vocal",
    "choir": "vocal",
    "fx": "fx",
    "sfx": "fx",
    "effect": "fx",
    "effects": "fx",
    "melody": "melody",
    "melodic": "melody",
    "lead": "melody",
    "leads": "melody",
    "chord": "chord",
    "chords": "chord",
    "stab": "chord",
    "stabs": "chord",
    "arp": "arp",
    "arps": "arp",
    "arpeggio": "arp",
    "rhythm": "rhythm",
    "rhythmic": "rhythm",
    "groove": "rhythm",
    "texture": "texture",
    "textures": "texture",
    "atmos": "texture",
    "atmosphere": "texture",
    "ambient": "texture",
    "ambience": "texture",
    "riser": "riser",
    "risers": "riser",
    "rise": "riser",
    "impact": "impact",
    "impacts": "impact",
    "sweep": "sweep",
    "sweeps": "sweep",
    "whoosh": "sweep",
}


@dataclass(frozen=True, slots=True)
class TagHit:
    slug: str
    facet: str
    source: str


@dataclass(frozen=True, slots=True)
class Inference:
    relative_path: str
    bpm: float | None = None
    key: str | None = None
    audio_is_loop: bool | None = None
    audio_bpm: float | None = None
    tags: tuple[TagHit, ...] = ()


def check_tag(slug: str) -> None:
    if slug not in CANONICAL_TAGS:
        raise ValueError("invalid tag")


def facet_for(slug: str) -> str:
    check_tag(slug)
    return SLUG_FACET[slug]


def ordered_slugs(slugs: Iterable[str]) -> list[str]:
    unique = [slug for slug in dict.fromkeys(slugs) if slug in CANONICAL_TAGS]
    return sorted(unique, key=lambda slug: (FACET_ORDER.index(SLUG_FACET[slug]), slug))


def match_tags(text: str, source: str) -> tuple[TagHit, ...]:
    blob = f" {_normalize(text)} "
    hits: dict[str, TagHit] = {}
    for alias in _ALIASES_LONGEST_FIRST:
        needle = f" {_normalize(alias)} "
        if needle not in blob:
            continue
        slug = _ALIAS_SLUG[alias]
        hits.setdefault(slug, TagHit(slug=slug, facet=SLUG_FACET[slug], source=source))
    return tuple(hits[slug] for slug in ordered_slugs(hits))


def merge_inferred_tags(
    *,
    path_tags: Sequence[TagHit],
    filename_tags: Sequence[TagHit],
    duration_seconds: float | None,
    audio_is_loop: bool | None,
) -> tuple[TagHit, ...]:
    merged: dict[str, TagHit] = {}
    for hit in path_tags:
        if hit.facet != FACET_FORM:
            merged[hit.slug] = hit
    for hit in filename_tags:
        if hit.facet != FACET_FORM:
            merged[hit.slug] = hit
    form = _merge_form(path_tags, filename_tags, duration_seconds, audio_is_loop)
    if form is not None:
        merged[form.slug] = form
    return tuple(merged[slug] for slug in ordered_slugs(merged))


def _merge_form(
    path_tags: Sequence[TagHit],
    filename_tags: Sequence[TagHit],
    duration_seconds: float | None,
    audio_is_loop: bool | None,
) -> TagHit | None:
    if duration_seconds is not None and duration_seconds < ONE_SHOT_MAX_SECONDS:
        return TagHit(slug="one-shot", facet=FACET_FORM, source=SOURCE_DURATION)
    if audio_is_loop is True:
        return TagHit(slug="loop", facet=FACET_FORM, source=SOURCE_ESTIMATOR)
    if audio_is_loop is False:
        return TagHit(slug="one-shot", facet=FACET_FORM, source=SOURCE_ESTIMATOR)
    filename_form = _form_hit(filename_tags)
    if filename_form is not None:
        return filename_form
    return _form_hit(path_tags)


def _form_hit(hits: Sequence[TagHit]) -> TagHit | None:
    for hit in hits:
        if hit.facet == FACET_FORM:
            return hit
    return None


def _normalize(text: str) -> str:
    chars: list[str] = []
    previous_space = True
    for raw in text.lower():
        if raw.isalnum():
            chars.append(raw)
            previous_space = False
            continue
        if not previous_space:
            chars.append(" ")
            previous_space = True
    return "".join(chars).strip()


_ALIASES_LONGEST_FIRST = tuple(
    sorted(_ALIAS_SLUG, key=lambda alias: (-len(_normalize(alias).split()), -len(alias), alias))
)
