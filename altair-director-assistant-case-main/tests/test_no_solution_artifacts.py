"""В студенческий репозиторий нельзя класть готовый ответ наставника."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SUFFIXES = {".pt", ".safetensors", ".bin", ".onnx"}
FORBIDDEN_NAMES = {
    "metadata.csv",
    "chaika_project.json",
    "groza_project.json",
    "project.json",
}
FORBIDDEN_PARTS = {
    "streamlit_app",
    "chaika.txt",
    "groza.txt",
    "hamlet.txt",
    "cherry_orchard.txt",
}


def test_case_has_no_solution_artifacts():
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(".git/"):
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            hits.append(rel)
        if path.name.lower() in {name.lower() for name in FORBIDDEN_NAMES}:
            hits.append(rel)
        lowered = rel.lower()
        for part in FORBIDDEN_PARTS:
            if part in lowered:
                hits.append(rel)
        if path.suffix.lower() == ".json" and "project" in path.name.lower():
            hits.append(rel)
    assert hits == [], f"solution artifacts in -case: {hits}"
