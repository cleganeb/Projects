"""Unpack the MAESTRO index CSV from the local zip. Do not re-download.

Looks up MAESTRO_ZIP, raw/, sibling cache/. Does not pick a hypothesis subset.
Do not commit the zip.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.download import mark_ready
from src.paths import DATA, resolve_maestro_zip


def main() -> None:
    zip_path = resolve_maestro_zip()
    print(f"zip {zip_path} {zip_path.stat().st_size} bytes (no download)", flush=True)
    index = DATA / "maestro_index.csv"
    with zipfile.ZipFile(zip_path) as zf:
        inner = next(n for n in zf.namelist() if n.endswith("maestro-v3.0.0.csv"))
        tmp = index.with_name(index.name + ".part")
        tmp.write_bytes(zf.read(inner))
        if not tmp.is_file() or tmp.stat().st_size == 0:
            raise RuntimeError("empty MAESTRO csv")
        tmp.replace(index)
    mark_ready(DATA / "maestro_index.READY.txt", [index, zip_path])
    print("index:", index)
    print("license: CC BY-NC-SA 4.0 — NC and SA attach to a finetuned checkpoint")
    print("pick rows from the csv and extract those midi paths from the zip yourself")
    print("do not commit the zip")


if __name__ == "__main__":
    main()
