import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_postings() -> list[dict]:
    with open(DATA_DIR / "job_postings.json") as f:
        return json.load(f)


def build_skill_index(postings: list[dict]) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for posting in postings:
        for skill in posting["required_skills"] + posting["nice_to_have_skills"]:
            index.setdefault(skill, []).append(posting)
    return index
