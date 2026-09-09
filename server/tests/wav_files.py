import math
import struct
import wave
from pathlib import Path


def write_sine_wav(
    path: Path,
    *,
    seconds: float = 0.1,
    frequency: int = 80,
    sample_rate: int = 44100,
    channels: int = 1,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(sample_rate * seconds)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for index in range(frame_count):
            sample = int(
                max(-1.0, min(1.0, math.sin(2 * math.pi * frequency * index / sample_rate)))
                * 32767
            )
            frames += struct.pack("<h", sample) * channels
        wav_file.writeframes(frames)
