from backend.data_loader import load_postings
from backend.scorer import get_gaps


postings = load_postings()


def test_gaps_sorted_by_momentum():
    user_skills = ["Python", "AWS", "Docker", "Git"]
    gaps = get_gaps(user_skills, "Cloud Security Engineer", postings)

    assert len(gaps) > 0
    for g in gaps:
        assert "skill" in g
        assert "momentum_score" in g
        assert "frequency_pct" in g
        assert "trend" in g

    scores = [g["momentum_score"] for g in gaps]
    assert scores == sorted(scores, reverse=True)


def test_empty_user_skills_returns_all_gaps():
    gaps = get_gaps([], "Cloud Security Engineer", postings)
    assert isinstance(gaps, list)
    assert len(gaps) > 0


def test_no_gaps_when_all_skills_known():
    role = "SOC Analyst"
    role_postings = [p for p in postings if role.lower() in p["title"].lower()]
    all_required = set()
    for p in role_postings:
        all_required.update(p["required_skills"])

    gaps = get_gaps(list(all_required), role, postings)
    assert gaps == []
