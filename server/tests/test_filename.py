import pytest

from app.catalog.meta import canonical_key
from app.catalog.tags import TagHit, merge_inferred_tags
from app.indexer.filename import parse_filename, parse_relative


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


def _slugs(hits: tuple[TagHit, ...]) -> list[str]:
    return [hit.slug for hit in hits]


@pytest.mark.parametrize(
    ("name", "filename_slugs"),
    [
        ("kick.wav", ["kick"]),
        ("Loop_128bpm_Cmin.wav", ["loop"]),
        ("c maj pad.wav", ["pad"]),
        ("Bbm_lead.wav", ["melody"]),
        ("80s_synth.wav", ["synth"]),
        ("Cinematic_riser.wav", ["riser"]),
        ("Ambience.wav", ["texture"]),
        ("808_snare.wav", ["snare"]),
        ("909_hat.wav", ["hat"]),
        ("open_hat.wav", ["hat"]),
        ("one-shot_os.wav", ["one-shot"]),
        ("Cmaj7_stab.wav", ["chord"]),
        ("A_melody.wav", ["melody"]),
        ("synth_melody_loop.wav", ["loop", "synth", "melody"]),
        ("hat_ride_oneshot.wav", ["one-shot", "hat", "ride"]),
        ("take_01.wav", []),
        ("key C# minor take.wav", []),
        ("808.wav", []),
    ],
)
def test_parse_filename_tags(name: str, filename_slugs: list[str]) -> None:
    parsed = parse_filename(name)
    assert _slugs(parsed.filename_tags) == filename_slugs
    assert not parsed.path_tags


def test_parse_relative_reads_folder_and_basename_tokens() -> None:
    parsed = parse_relative("Loops/Melodic/synth_pluck.wav")
    assert _slugs(parsed.path_tags) == ["loop", "melody"]
    assert _slugs(parsed.filename_tags) == ["synth"]


def test_parse_relative_maps_drum_folders() -> None:
    parsed = parse_relative("Drums/Kicks/acoustic_kick.wav")
    assert _slugs(parsed.path_tags) == ["kick"]
    assert _slugs(parsed.filename_tags) == ["kick"]


def test_generic_folder_names_are_not_tags() -> None:
    parsed = parse_relative("Samples/WAV/take_01.wav")
    assert not parsed.path_tags
    assert not parsed.filename_tags


def test_merge_prefers_short_duration_over_loop_filename() -> None:
    parsed = parse_filename("Loop_kick.wav")
    merged = merge_inferred_tags(
        path_tags=parsed.path_tags,
        filename_tags=parsed.filename_tags,
        duration_seconds=0.2,
        audio_is_loop=True,
    )
    assert _slugs(merged) == ["one-shot", "kick"]
    assert merged[0].source == "duration"


def test_merge_prefers_estimator_over_folder_form() -> None:
    parsed = parse_relative("Loops/Hats/closed_hat.wav")
    merged = merge_inferred_tags(
        path_tags=parsed.path_tags,
        filename_tags=parsed.filename_tags,
        duration_seconds=4.0,
        audio_is_loop=False,
    )
    assert "one-shot" in _slugs(merged)
    assert "loop" not in _slugs(merged)
    assert merged[0].source == "estimator"


def test_merge_unions_role_and_function_from_path_and_name() -> None:
    parsed = parse_relative("Loops/Melodic/hat_ride.wav")
    merged = merge_inferred_tags(
        path_tags=parsed.path_tags,
        filename_tags=parsed.filename_tags,
        duration_seconds=8.0,
        audio_is_loop=None,
    )
    assert _slugs(merged) == ["loop", "hat", "ride", "melody"]
    sources = {hit.slug: hit.source for hit in merged}
    assert sources["loop"] == "path"
    assert sources["melody"] == "path"
    assert sources["hat"] == "filename"
