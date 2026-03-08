from backend.data_loader import build_skill_index


def compute_momentum_scores(postings: list[dict]) -> dict[str, float]:
    index = build_skill_index(postings)
    total = len(postings)
    scores: dict[str, float] = {}

    for skill, skill_postings in index.items():
        frequency_score = len(skill_postings) / total
        recency_score = sum(p["posted_month"] for p in skill_postings) / (len(skill_postings) * 12)
        scores[skill] = (0.6 * frequency_score) + (0.4 * recency_score)

    return dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))


def _recency_score(skill: str, index: dict[str, list[dict]]) -> float:
    skill_postings = index.get(skill, [])
    if not skill_postings:
        return 0.0
    return sum(p["posted_month"] for p in skill_postings) / (len(skill_postings) * 12)


def _trend_label(recency: float) -> str:
    if recency > 0.6:
        return "rising"
    if recency >= 0.4:
        return "stable"
    return "declining"


def get_gaps(
    user_skills: list[str],
    target_role: str,
    postings: list[dict],
) -> list[dict]:
    role_lower = target_role.lower()
    filtered = [p for p in postings if role_lower in p["title"].lower()]

    if not filtered:
        filtered = postings

    required_skills: set[str] = set()
    for posting in filtered:
        required_skills.update(posting["required_skills"])

    user_skills_lower = {s.lower() for s in user_skills}
    gap_skills = {s for s in required_skills if s.lower() not in user_skills_lower}

    momentum = compute_momentum_scores(postings)
    index = build_skill_index(postings)
    total = len(postings)

    gaps: list[dict] = []
    for skill in gap_skills:
        recency = _recency_score(skill, index)
        gaps.append({
            "skill": skill,
            "momentum_score": round(momentum.get(skill, 0.0), 4),
            "frequency_pct": round(len(index.get(skill, [])) / total * 100, 1),
            "trend": _trend_label(recency),
        })

    gaps.sort(key=lambda g: g["momentum_score"], reverse=True)
    return gaps
