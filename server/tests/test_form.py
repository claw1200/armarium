from pathlib import Path

from app.indexer.form import FormEstimate, _parse_estimate, estimate_form, should_estimate_form


def test_should_estimate_form_skips_short_long_and_non_wav() -> None:
    assert should_estimate_form("wav", 1.0) is True
    assert should_estimate_form("aiff", 8.0) is True
    assert should_estimate_form("wav", 0.5) is False
    assert should_estimate_form("wav", 61.0) is False
    assert should_estimate_form("mp3", 4.0) is False
    assert should_estimate_form("wav", None) is False


def test_parse_estimate_reads_loop_json() -> None:
    assert _parse_estimate('{"loop":true,"bpm":128}') == FormEstimate(True, 128.0)
    assert _parse_estimate('{"loop":false}') == FormEstimate(False, None)
    assert _parse_estimate("nope") == FormEstimate(None, None)
    assert _parse_estimate('{"loop":"yes"}') == FormEstimate(None, None)


def test_missing_estimator_binary_is_inconclusive(tmp_path: Path) -> None:
    path = tmp_path / "kick.wav"
    path.write_bytes(b"RIFF")
    assert estimate_form(path, command="armarium-loop-tempo-missing") == FormEstimate(
        None, None
    )
