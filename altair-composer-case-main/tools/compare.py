"""Compare two MIDI continuations of the same motif.

    python tools/compare.py outputs/a.mid outputs/b.mid --motif data/motifs/motif_leap.mid
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.metrics import continuation_events, melody_stats, motif_recall


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("midi", nargs="+", type=Path, help="два или больше MIDI")
    parser.add_argument("--motif", type=Path, required=True)
    args = parser.parse_args()
    if len(args.midi) < 2:
        raise SystemExit("нужны минимум два MIDI")
    motif = args.motif
    if not motif.is_file():
        raise SystemExit(f"нет мотива {motif}")
    for path in args.midi:
        if not path.is_file():
            raise SystemExit(f"нет файла {path}")
        tail = continuation_events(path, motif)
        stats = melody_stats(path, events=tail)
        recall = motif_recall(motif, path)
        print(
            f"{path.name:28} notes={stats['n_notes']:3} "
            f"range={stats['pitch_range']:3} dens={stats['notes_per_16']} "
            f"iv={stats['mean_abs_interval']} recall={recall}"
        )


if __name__ == "__main__":
    main()
