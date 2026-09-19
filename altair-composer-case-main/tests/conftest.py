from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def tmp_midi_dir(tmp_path: Path) -> Path:
    d = tmp_path / "midi"
    d.mkdir()
    return d
