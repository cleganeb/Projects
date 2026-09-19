import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MOTIFS = DATA / "motifs"
OUTPUTS = ROOT / "outputs"
MAESTRO_ZIP_URL = "https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0-midi.zip"
MAESTRO_ZIP_NAME = "maestro-v3.0.0-midi.zip"


def resolve_maestro_zip() -> Path:
    env = os.environ.get("MAESTRO_ZIP", "").strip()
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(ROOT / "raw" / MAESTRO_ZIP_NAME)
    candidates.append(ROOT.parent / "cache" / MAESTRO_ZIP_NAME)
    candidates.append(Path.home() / "Desktop" / "altair" / "cache" / MAESTRO_ZIP_NAME)
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return path
    raise FileNotFoundError(
        "MAESTRO zip not found. Set MAESTRO_ZIP or put the file in raw/ "
        f"or Desktop/altair/cache/{MAESTRO_ZIP_NAME}. "
        f"Upstream URL (reference only): {MAESTRO_ZIP_URL}"
    )
