"""Melody extract / tokenize / MIDI round-trip."""

from pathlib import Path

import mido

from src.tokenize_midi import (
    DURATIONS,
    events_to_midi,
    events_to_tokens,
    extract_melody_events,
    tokens_to_events,
    write_midi,
)


def _monophonic_midi(path: Path, pitches: list[int], duration_ticks: int = 240) -> Path:
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    for i, p in enumerate(pitches):
        track.append(mido.Message("note_on", note=p, velocity=80, time=0 if i else 0))
        track.append(mido.Message("note_off", note=p, velocity=0, time=duration_ticks))
    mid.save(path)
    return path


def test_extract_melody_takes_highest_of_chord(tmp_path: Path) -> None:
    path = tmp_path / "chord.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    for p in (60, 64, 67):
        track.append(mido.Message("note_on", note=p, velocity=80, time=0))
    for i, p in enumerate((60, 64, 67)):
        track.append(mido.Message("note_off", note=p, velocity=0, time=480 if i == 0 else 0))
    mid.save(path)
    events = extract_melody_events(path)
    pitches = [p for p, _d in events if p is not None]
    assert pitches == [67]


def test_tokens_roundtrip_preserves_pitch_sequence(tmp_path: Path) -> None:
    path = _monophonic_midi(tmp_path / "scale.mid", [60, 62, 64, 65, 67])
    events = extract_melody_events(path)
    tokens = events_to_tokens(events)
    restored = tokens_to_events(tokens)
    assert [p for p, _ in restored] == [p for p, _ in events]


def test_duration_snaps_to_allowed_grid() -> None:
    events = [(60, 5), (None, 7), (64, 40)]
    restored = tokens_to_events(events_to_tokens(events))
    for _p, dur in restored:
        assert dur in DURATIONS


def test_write_midi_is_readable(tmp_path: Path) -> None:
    out = tmp_path / "out.mid"
    events = [(60, 4), (64, 4), (67, 8)]
    write_midi(events_to_midi(events), out)
    assert out.is_file() and out.stat().st_size > 0
    again = extract_melody_events(out)
    assert [p for p, _ in again] == [60, 64, 67]
