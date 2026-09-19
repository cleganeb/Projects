"""License allowlist and work-id isolated splits."""

import pytest

from src.catalog import assign_splits, is_allowed_license, reject_unlicensed


def test_unknown_license_is_rejected() -> None:
    assert is_allowed_license("PD") is True
    assert is_allowed_license("CC-BY-SA-4.0") is True
    assert is_allowed_license("CC BY-NC-SA 4.0") is True
    assert is_allowed_license("") is False
    assert is_allowed_license("unknown") is False
    assert is_allowed_license("all rights reserved") is False
    assert is_allowed_license("lakh-unverified") is False


def test_reject_unlicensed_drops_unclear_rows() -> None:
    rows = [
        {"file": "a.mid", "license": "PD", "work_id": "w1"},
        {"file": "b.mid", "license": "", "work_id": "w2"},
        {"file": "c.mid", "license": "unknown", "work_id": "w3"},
        {"file": "d.mid", "license": "CC-BY-NC-SA-4.0", "work_id": "w4"},
    ]
    kept, dropped = reject_unlicensed(rows)
    assert {r["file"] for r in kept} == {"a.mid", "d.mid"}
    assert {r["file"] for r in dropped} == {"b.mid", "c.mid"}


def test_split_keeps_whole_work_in_one_part() -> None:
    rows = []
    for work in [f"piece_{i:02d}" for i in range(20)]:
        for excerpt in (0, 1, 2):
            rows.append({"work_id": work, "file": f"{work}_{excerpt}.mid"})
    tagged = assign_splits(rows, key="work_id", ratios=(0.7, 0.15, 0.15), seed=21)
    by_work: dict[str, set[str]] = {}
    for row in tagged:
        by_work.setdefault(row["work_id"], set()).add(row["split"])
    for work, splits in by_work.items():
        assert len(splits) == 1, f"{work} leaked across {splits}"
    assert {row["split"] for row in tagged} == {"train", "val", "test"}


def test_split_requires_work_id() -> None:
    with pytest.raises(ValueError):
        assign_splits([{"file": "x.mid"}], key="work_id")
