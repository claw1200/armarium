from pathlib import Path

from app.indexer.audio import AudioInfo, read_audio_info
from tests.wav_files import write_sine_wav


def test_read_audio_info_from_wav(tmp_path: Path) -> None:
    path = tmp_path / "kick.wav"
    write_sine_wav(path, seconds=0.2, sample_rate=44100, channels=1)
    info = read_audio_info(path)
    assert info.sample_rate == 44100
    assert info.channels == 1
    assert info.duration_seconds is not None
    assert 0.15 < info.duration_seconds < 0.25


def test_read_audio_info_skips_non_audio(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("not audio", encoding="utf-8")
    info = read_audio_info(path)
    assert info == AudioInfo(None, None, None)
