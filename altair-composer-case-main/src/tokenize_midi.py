"""Monophonic melody as (pitch, duration) events and a small token vocab."""

from __future__ import annotations

from pathlib import Path

import mido

PAD = 0
BOS = 1
EOS = 2
REST = 3
PITCH_0 = 4
N_PITCH = 128
DURATIONS = (1, 2, 3, 4, 6, 8, 12, 16, 24, 32)
DUR_BASE = PITCH_0 + N_PITCH
VOCAB_SIZE = DUR_BASE + len(DURATIONS)
_DUR_INDEX = {d: i for i, d in enumerate(DURATIONS)}


def pitch_token(midi_pitch: int) -> int:
    if not 0 <= midi_pitch <= 127:
        raise ValueError(f"pitch out of range: {midi_pitch}")
    return PITCH_0 + midi_pitch


def dur_token(sixteenths: int) -> int:
    return DUR_BASE + _DUR_INDEX[snap_duration(sixteenths)]


def snap_duration(n: int) -> int:
    if n < 1:
        n = 1
    if n in _DUR_INDEX:
        return n
    if n > DURATIONS[-1]:
        return DURATIONS[-1]
    return min(DURATIONS, key=lambda d: (abs(d - n), d))


def _sixteenths(ticks: int, ticks_per_beat: int) -> int:
    grid = max(ticks_per_beat / 4.0, 1.0)
    return max(1, int(round(ticks / grid)))


def extract_melody_events(path: Path | str) -> list[tuple[int | None, int]]:
    mid = mido.MidiFile(str(path))
    tpb = mid.ticks_per_beat or 480
    abs_t = 0
    active: dict[int, int] = {}
    last_t = 0
    last_pitch: int | None = None
    started = False
    events: list[tuple[int | None, int]] = []

    def current_pitch() -> int | None:
        return max(active) if active else None

    def emit(until: int) -> None:
        nonlocal last_t, last_pitch, started
        if until <= last_t:
            return
        if not started and last_pitch is None:
            last_t = until
            return
        started = True
        remaining = _sixteenths(until - last_t, tpb)
        while remaining > 0:
            chunk = min(remaining, DURATIONS[-1])
            events.append((last_pitch, snap_duration(chunk)))
            remaining -= chunk
        last_t = until

    for msg in mido.merge_tracks(mid.tracks):
        abs_t += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            emit(abs_t)
            active[msg.note] = active.get(msg.note, 0) + 1
            last_pitch = current_pitch()
        elif msg.type in {"note_off", "note_on"}:
            emit(abs_t)
            if msg.note in active:
                active[msg.note] -= 1
                if active[msg.note] <= 0:
                    del active[msg.note]
            last_pitch = current_pitch()
    emit(abs_t)
    return [(p, d) for p, d in events if d > 0]


def events_to_tokens(events: list[tuple[int | None, int]]) -> list[int]:
    tokens = [BOS]
    for pitch, dur in events:
        remaining = max(int(dur), 1)
        while remaining > 0:
            chunk = min(remaining, DURATIONS[-1])
            snapped = snap_duration(chunk)
            tokens.append(REST if pitch is None else pitch_token(int(pitch)))
            tokens.append(dur_token(snapped))
            remaining -= snapped
    tokens.append(EOS)
    return tokens


def tokens_to_events(tokens: list[int]) -> list[tuple[int | None, int]]:
    events: list[tuple[int | None, int]] = []
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t in (PAD, BOS, EOS):
            i += 1
            continue
        pitch: int | None
        if t == REST:
            pitch = None
        elif PITCH_0 <= t < DUR_BASE:
            pitch = t - PITCH_0
        else:
            i += 1
            continue
        dur = 4
        if i + 1 < n and DUR_BASE <= tokens[i + 1] < VOCAB_SIZE:
            dur = DURATIONS[tokens[i + 1] - DUR_BASE]
            i += 2
        else:
            i += 1
        events.append((pitch, dur))
    return events


def events_to_midi(
    events: list[tuple[int | None, int]],
    ticks_per_beat: int = 480,
    tempo: int = 500000,
) -> mido.MidiFile:
    mid = mido.MidiFile(ticks_per_beat=ticks_per_beat)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    wait = 0
    ticks_16 = ticks_per_beat // 4
    for pitch, dur in events:
        ticks = int(dur) * ticks_16
        if pitch is None:
            wait += ticks
            continue
        track.append(mido.Message("note_on", note=int(pitch), velocity=80, time=wait))
        track.append(mido.Message("note_off", note=int(pitch), velocity=0, time=ticks))
        wait = 0
    track.append(mido.MetaMessage("end_of_track", time=wait))
    return mid


def chunk_events(
    events: list[tuple[int | None, int]],
    size: int = 24,
    hop: int = 16,
) -> list[list[tuple[int | None, int]]]:
    if not events:
        return []
    if len(events) <= size:
        return [events]
    out = []
    i = 0
    while i < len(events):
        chunk = events[i : i + size]
        n_notes = sum(1 for p, _d in chunk if p is not None)
        if n_notes >= 4:
            out.append(chunk)
        if i + size >= len(events):
            break
        i += hop
    return out


def write_midi(mid: mido.MidiFile, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    mid.save(tmp)
    if not tmp.is_file() or tmp.stat().st_size == 0:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"MIDI was not written: {path}")
    tmp.replace(path)
    return path
