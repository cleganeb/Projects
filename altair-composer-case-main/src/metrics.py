"""Simple musical stats on a monophonic melody."""

from __future__ import annotations

from pathlib import Path

from src.tokenize_midi import extract_melody_events


def melody_stats(path: Path | str, events=None) -> dict:
    events = list(events) if events is not None else extract_melody_events(path)
    notes = [(p, d) for p, d in events if p is not None]
    rests = [(p, d) for p, d in events if p is None]
    pitches = [p for p, _ in notes]
    durs = [d for _p, d in notes]
    n = len(notes)
    total_16 = sum(d for _p, d in events) or 1
    intervals = [abs(pitches[i] - pitches[i - 1]) for i in range(1, len(pitches))]
    bigrams = list(zip(pitches, pitches[1:]))
    return {
        "file": Path(path).name,
        "n_notes": n,
        "n_rests": len(rests),
        "duration_sixteenths": int(total_16),
        "notes_per_16": round(n / total_16, 4),
        "pitch_min": min(pitches) if pitches else "",
        "pitch_max": max(pitches) if pitches else "",
        "pitch_range": (max(pitches) - min(pitches)) if pitches else 0,
        "mean_abs_interval": round(sum(intervals) / len(intervals), 3) if intervals else 0,
        "mean_duration": round(sum(durs) / len(durs), 3) if durs else 0,
        "unique_pitches": len(set(pitches)),
        "pitch_bigrams": bigrams,
    }


def continuation_events(full_path: Path | str, motif_path: Path | str):
    full = extract_melody_events(full_path)
    motif = extract_melody_events(motif_path)
    n = len(motif)
    return full[n:] if len(full) > n else full


def motif_recall(motif_path: Path | str, continuation_path: Path | str) -> float:
    motif = melody_stats(motif_path)
    tail = continuation_events(continuation_path, motif_path)
    cont = melody_stats(continuation_path, events=tail)
    m = set(motif["pitch_bigrams"])
    if not m:
        return 0.0
    c = set(cont["pitch_bigrams"])
    return round(len(m & c) / len(m), 3)


def row_for_csv(stats: dict, extra: dict | None = None) -> dict:
    out = {k: v for k, v in stats.items() if k != "pitch_bigrams"}
    if extra:
        out.update(extra)
    return out
