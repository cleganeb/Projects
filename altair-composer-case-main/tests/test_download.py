"""Ready-marker only after the file is on disk; per-item errors do not wipe the rest."""

from pathlib import Path

import pytest

from src.corpus import process_items
from src.download import download_file, mark_ready


def test_mark_ready_refuses_missing_files(tmp_path: Path) -> None:
    marker = tmp_path / "READY.txt"
    missing = tmp_path / "nope.mid"
    with pytest.raises(RuntimeError, match="missing"):
        mark_ready(marker, [missing])
    assert not marker.exists()


def test_mark_ready_after_files_exist(tmp_path: Path) -> None:
    f = tmp_path / "a.mid"
    f.write_bytes(b"MThd")
    marker = tmp_path / "READY.txt"
    mark_ready(marker, [f])
    assert marker.read_text(encoding="utf-8").strip() == "ready"


def test_download_writes_file_before_return(tmp_path: Path) -> None:
    src = tmp_path / "remote.mid"
    src.write_bytes(b"MIDI-BYTES")
    dest = tmp_path / "out" / "local.mid"

    def opener(url: str):
        class _Resp:
            def read(self, n: int = -1) -> bytes:
                data = src.read_bytes()
                self.read = lambda _n=-1: b""  # type: ignore[method-assign]
                return data

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return _Resp()

    seen_before = {"exists": False}

    class TrackingOpener:
        def __init__(self):
            self._inner = opener

        def __call__(self, url: str):
            inner = opener(url)

            class Wrap:
                def read(self, n: int = -1) -> bytes:
                    return inner.read(n)

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    seen_before["exists"] = dest.exists()
                    return False

            return Wrap()

    result = download_file("http://example.test/x.mid", dest, opener=TrackingOpener())
    assert result == dest
    assert dest.is_file()
    assert dest.read_bytes() == b"MIDI-BYTES"
    assert dest.with_name(dest.name + ".part").exists() is False


def test_process_items_keeps_going_after_one_error() -> None:
    def fn(x: int) -> int:
        if x == 2:
            raise ValueError("bad midi")
        return x * 10

    ok, errors = process_items([1, 2, 3], fn)
    assert ok == [10, 30]
    assert len(errors) == 1
    assert errors[0][0] == 2
