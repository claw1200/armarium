from dataclasses import dataclass
from pathlib import Path

import mutagen
from mutagen import MutagenError


@dataclass(frozen=True, slots=True)
class AudioInfo:
    duration_seconds: float | None
    sample_rate: int | None
    channels: int | None


def read_audio_info(path: Path) -> AudioInfo:
    try:
        audio = mutagen.File(path)
    except MutagenError:
        return AudioInfo(None, None, None)
    if audio is None or audio.info is None:
        return AudioInfo(None, None, None)
    info = audio.info
    duration = getattr(info, "length", None)
    sample_rate = getattr(info, "sample_rate", None)
    channels = getattr(info, "channels", None)
    return AudioInfo(
        duration_seconds=float(duration) if duration is not None else None,
        sample_rate=int(sample_rate) if sample_rate is not None else None,
        channels=int(channels) if channels is not None else None,
    )
