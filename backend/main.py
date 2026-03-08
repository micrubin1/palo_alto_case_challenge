from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.data_loader import load_postings
from backend.scorer import compute_momentum_scores, get_gaps
from backend.ai_engine import parse_resume, generate_roadmap_item

app = FastAPI(title="Skill Futures API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

postings = load_postings()
momentum_table = compute_momentum_scores(postings)


class AnalyzeRequest(BaseModel):
    resume_text: str
    target_role: str


def _recency_score(skill: str) -> float:
    from backend.data_loader import build_skill_index

    index = build_skill_index(postings)
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/skills/momentum")
def skills_momentum():
    results = []
    for skill, score in momentum_table.items():
        recency = _recency_score(skill)
        results.append({
            "skill": skill,
            "momentum_score": round(score, 4),
            "trend": _trend_label(recency),
        })
    return results


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    user_skills = parse_resume(req.resume_text)
    gaps = get_gaps(user_skills, req.target_role, postings)

    top_gaps_roadmap = []
    for gap in gaps[:3]:
        roadmap = generate_roadmap_item(
            gap["skill"], gap["momentum_score"], req.target_role
        )
        top_gaps_roadmap.append({
            "skill": gap["skill"],
            "momentum_score": gap["momentum_score"],
            "trend": gap["trend"],
            **roadmap,
        })

    return {
        "extracted_skills": user_skills,
        "gaps_ranked": gaps,
        "top_gaps_roadmap": top_gaps_roadmap,
    }
