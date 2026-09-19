"""Download to a temp file; READY marker only after bytes are on disk."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
from urllib.request import urlopen

Opener = Callable[[str], object]


def download_file(
    url: str,
    dest: Path | str,
    opener: Opener | None = None,
    timeout: int = 60,
) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    open_fn = opener or (lambda u: urlopen(u, timeout=timeout))
    try:
        with open_fn(url) as resp, tmp.open("wb") as out:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out.write(chunk)
        if not tmp.is_file() or tmp.stat().st_size == 0:
            raise RuntimeError(f"empty download: {url}")
        tmp.replace(dest)
        if not dest.is_file() or dest.stat().st_size == 0:
            raise RuntimeError(f"file missing after write: {dest}")
        return dest
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def mark_ready(marker: Path | str, required_files: list[Path | str]) -> Path:
    marker = Path(marker)
    missing = [
        str(p)
        for p in required_files
        if not Path(p).is_file() or Path(p).stat().st_size == 0
    ]
    if missing:
        raise RuntimeError("cannot mark ready, missing: " + ", ".join(missing))
    marker.write_text("ready\n", encoding="utf-8")
    return marker
