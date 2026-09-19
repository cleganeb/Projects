"""Write a monophonic note list to a MIDI file. Not an OMR model."""

from __future__ import annotations

from pathlib import Path

import mido


def write_notes_midi(
    notes: list[tuple[int, float, float]],
    path: Path,
    tempo: int = 120,
) -> None:
    """notes: (midi_pitch, start_beats, duration_beats). File exists before return."""
    path = Path(path)
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo), time=0))
    events: list[tuple[float, int, str, int]] = []
    for pitch, start, dur in notes:
        events.append((start, 1, "on", int(pitch)))
        events.append((start + dur, 0, "off", int(pitch)))
    events.sort()
    last = 0.0
    for t, _order, kind, pitch in events:
        dt = max(int(round((t - last) * 480)), 0)
        if kind == "on":
            track.append(mido.Message("note_on", note=pitch, velocity=80, time=dt))
        else:
            track.append(mido.Message("note_off", note=pitch, velocity=64, time=dt))
        last = t
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    mid.save(str(tmp))
    tmp.replace(path)
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"midi was not written: {path}")
