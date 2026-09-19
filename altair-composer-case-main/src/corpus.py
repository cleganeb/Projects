"""Per-item processing: one bad MIDI must not wipe the rest of the corpus."""

from __future__ import annotations

from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def process_items(
    items: Iterable[T],
    fn: Callable[[T], R],
) -> tuple[list[R], list[tuple[T, BaseException]]]:
    ok: list[R] = []
    errors: list[tuple[T, BaseException]] = []
    for item in items:
        try:
            ok.append(fn(item))
        except BaseException as exc:  # noqa: BLE001 — keep going on a single bad file
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            errors.append((item, exc))
    return ok, errors
