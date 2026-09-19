"""Load and save score images. cv2.imread breaks on non-ASCII Windows paths."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_score_image(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"cannot decode image: {path}")
    return image


def save_score_image(path: Path, image: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower() or ".png"
    ok, buf = cv2.imencode(suffix, image)
    if not ok:
        raise RuntimeError(f"imencode failed: {path}")
    path.write_bytes(buf.tobytes())
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"image was not written: {path}")
