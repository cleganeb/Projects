"""License allowlist, CSV with BOM, work-isolated splits."""

from __future__ import annotations

import csv
import random
import re
from pathlib import Path
from typing import Iterable

ALLOWED_LICENSES = frozenset(
    {
        "pd",
        "public-domain",
        "cc0",
        "cc-by",
        "cc-by-3.0",
        "cc-by-4.0",
        "cc-by-sa",
        "cc-by-sa-2.5",
        "cc-by-sa-3.0",
        "cc-by-sa-4.0",
        "cc-by-nc",
        "cc-by-nc-4.0",
        "cc-by-nc-sa",
        "cc-by-nc-sa-4.0",
        "mutopiabsd",
    }
)


def normalize_license(value: str | None) -> str:
    if not value:
        return ""
    text = value.strip().lower()
    text = text.replace("creativecommons", "cc")
    text = re.sub(r"https?://creativecommons.org/licenses/", "", text)
    text = text.replace("_", "-")
    text = re.sub(r"[^a-z0-9+\-.]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    aliases = {
        "publicdomain": "public-domain",
        "cc-by-sa-2-5": "cc-by-sa-2.5",
        "cc-by-sa-3-0": "cc-by-sa-3.0",
        "cc-by-sa-4-0": "cc-by-sa-4.0",
        "cc-by-nc-sa-4-0": "cc-by-nc-sa-4.0",
        "cc-by-4-0": "cc-by-4.0",
        "cc-by-3-0": "cc-by-3.0",
        "ccbysa": "cc-by-sa",
        "ccbyncsa": "cc-by-nc-sa",
    }
    return aliases.get(text, text)


def is_allowed_license(value: str | None) -> bool:
    return normalize_license(value) in ALLOWED_LICENSES


def reject_unlicensed(rows: Iterable[dict]) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    for row in rows:
        if is_allowed_license(row.get("license")):
            kept.append(row)
        else:
            dropped.append(row)
    return kept, dropped


def assign_splits(
    rows: list[dict],
    key: str = "work_id",
    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15),
    seed: int = 21,
) -> list[dict]:
    ids = []
    for row in rows:
        if not row.get(key):
            raise ValueError(f"missing {key} for {row.get('file')}")
        ids.append(row[key])
    unique = sorted(set(ids))
    rng = random.Random(seed)
    rng.shuffle(unique)
    n = len(unique)
    if n < 3:
        raise ValueError("need at least 3 works to fill train/val/test")
    n_train = max(1, int(round(n * ratios[0])))
    n_val = max(1, int(round(n * ratios[1])))
    if n_train + n_val >= n:
        n_train = max(1, n - 2)
        n_val = 1
    mapping = {}
    for i, work in enumerate(unique):
        if i < n_train:
            mapping[work] = "train"
        elif i < n_train + n_val:
            mapping[work] = "val"
        else:
            mapping[work] = "test"
    out = []
    for row in rows:
        tagged = dict(row)
        tagged["split"] = mapping[row[key]]
        out.append(tagged)
    return out


def write_csv(path: Path | str, rows: list[dict], fieldnames: list[str] | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        raise ValueError("nothing to write")
    names = fieldnames or list(rows[0].keys())
    tmp = path.with_name(path.name + ".part")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    tmp.replace(path)
    return path


def read_csv(path: Path | str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
