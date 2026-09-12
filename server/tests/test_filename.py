import pytest

from app.catalog.meta import canonical_key
from app.indexer.filename import parse_filename


@pytest.mark.parametrize(
    ("name", "bpm", "key"),
    [
        ("kick.wav", None, None),
        ("Loop_128bpm_Cmin.wav", 128.0, "Cm"),
        ("loop-120bpm-F#m.wav", 120.0, "F#m"),
        ("_120_bpm_.wav", 120.0, None),
        ("(Cm).wav", None, "Cm"),
        ("c maj pad.wav", None, "C"),
        ("c min.wav", None, "Cm"),
        ("Cmajor_90.wav", 90.0, "C"),
        ("Dbmin_140.wav", 140.0, "C#m"),
        ("Bbm_lead.wav", None, "A#m"),
        ("Kick_128BPM_C#m.wav", 128.0, "C#m"),
        ("80s_synth.wav", None, None),
        ("Cinematic_riser.wav", None, None),
        ("Ambience.wav", None, None),
        ("take_01.wav", None, None),
        ("808_snare.wav", None, None),
        ("909_hat.wav", None, None),
        ("snare_808bpm.wav", None, None),
        ("perc_12.wav", None, None),
        ("perc_12bpm.wav", None, None),
        ("kick_64bpm.wav", None, None),
        ("kick_65bpm.wav", 65.0, None),
        ("loop_240.wav", 240.0, None),
        ("loop_241bpm.wav", None, None),
        ("kick128bpm.wav", None, None),
        ("Cmaj7_stab.wav", None, None),
        ("Em_pad.wav", None, "Em"),
        ("loop in C.wav", None, "C"),
        ("128_Cmin.wav", 128.0, "Cm"),
        ("A_melody.wav", None, "A"),
        ("F#_pluck.wav", None, "F#"),
        ("key C# minor take.wav", None, "C#m"),
        ("120bpm_80.wav", 120.0, None),
        ("80_120bpm.wav", 120.0, None),
    ],
)
def test_parse_filename(name: str, bpm: float | None, key: str | None) -> None:
    parsed = parse_filename(name)
    assert parsed.bpm == bpm
    assert parsed.key == key


def test_canonical_key_normalizes_flats_and_modes() -> None:
    assert canonical_key("c") == "C"
    assert canonical_key("c#m") == "C#m"
    assert canonical_key("Db") == "C#"
    assert canonical_key("bb min") == "A#m"
    assert canonical_key("F# major") == "F#"
    assert canonical_key("E#") == "F"
    assert canonical_key("Cb") == "B"
    assert canonical_key("Amin") == "Am"
    assert canonical_key("Cmaj7") is None
    assert canonical_key("H") is None
