# Skill Futures

A career navigator that ranks skill gaps by market demand momentum — not just frequency — so candidates know which gaps to close first.

**Candidate:** Micah Rubin
**Scenario:** Skill-Bridge Career Navigator
**Estimated Time Spent:** 4 hours

---

## How It Works

1. User pastes a resume and selects a target role (e.g. Cloud Security Engineer)
2. Gemini AI extracts technical skills from the resume text
3. A scoring engine compares extracted skills against a synthetic job postings dataset
4. Each missing skill gets a **Demand Momentum Score** that combines posting frequency (how many jobs require it) with recency (whether demand is growing or declining)
5. The top 3 gaps get AI-generated learning roadmaps with specific resources and time estimates

The result: a prioritized, actionable plan — not a flat list of everything you're missing.

---



## Quick Start

### Prerequisites

- Python 3.10+
- A free Gemini API key from [aistudio.google.com](https://aistudio.google.com)

### Run

```bash
git clone <repo-url> && cd skill-futures
echo "GEMINI_API_KEY=your_key_here" > .env
pip install -r requirements.txt
python -m uvicorn backend.main:app --port 8000
```

Then open `frontend/index.html` in a browser. The sample resume is pre-loaded — click "Analyze My Skills" to see it work.

### Test

```bash
python -m pytest backend/tests/ -v
```

---

## Project Structure

```
skill-futures/
├── backend/
│   ├── main.py           # FastAPI app — 3 endpoints
│   ├── scorer.py         # Momentum scoring engine + gap analysis
│   ├── ai_engine.py      # Gemini integration with full fallback layer
│   ├── data_loader.py    # JSON data loading + skill indexing
│   └── tests/
│       ├── conftest.py
│       ├── test_scorer.py
│       └── test_ai_engine.py
├── data/
│   ├── job_postings.json # 70 synthetic postings, 4 roles, 79 unique skills
│   └── sample_resume.txt # Demo resume (Alex Chen, CS new-grad)
├── frontend/
│   └── index.html        # Single-file SPA (Tailwind + Chart.js via CDN)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Design Decisions

### Momentum Score: 0.6 Frequency / 0.4 Recency

The formula is `(0.6 × frequency_score) + (0.4 × recency_score)` where frequency is the share of postings requiring a skill and recency is the average posting month normalized to [0, 1].

Frequency is weighted higher because a skill that appears in 70% of postings is critical even if demand dipped slightly this quarter. Pure recency weighting would over-promote niche skills that spiked in a single recent month. The 60/40 split ensures established high-demand skills rank above flash-in-the-pan trends while still rewarding upward momentum.

### Model Choice: Gemini 2.5 Flash

Selected for the free tier availability, low latency (~1s per call), and sufficient capability for the two structured tasks the app needs: JSON skill extraction from resume text and generating short learning resource recommendations. A larger model would add latency and cost without meaningful quality improvement for these constrained prompts.

### Fallback Architecture

Every AI call has a deterministic fallback path:

- **Resume parsing** falls back to case-insensitive keyword matching against a list of 60 common tech skills
- **Roadmap generation** falls back to a curated dictionary of resources for high-momentum skills, or a generic search template for unknown skills
- **Gap analysis** (`get_gaps()`) is fully rule-based with no AI dependency — it always works

This matters for two reasons. First, reliability: the app returns useful results even if the API key is missing, the quota is exhausted, or the network is down. Second, Responsible AI: every AI-generated result is tagged with `ai_powered: true/false` in the API response and labeled in the UI, so the user always knows whether they're seeing an AI suggestion or a deterministic result.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analyze` | Parse resume, compute gaps, generate roadmap for top 3 |
| `GET` | `/skills/momentum` | Full momentum score table (all 79 skills) |
| `GET` | `/health` | Health check |

### POST /analyze

**Request:**
```json
{
  "resume_text": "paste resume here",
  "target_role": "Cloud Security Engineer"
}
```

**Response:**
```json
{
  "extracted_skills": ["Python", "AWS", "Docker", ...],
  "gaps_ranked": [
    {"skill": "SIEM Tools", "momentum_score": 0.711, "frequency_pct": 65.7, "trend": "rising"},
    ...
  ],
  "top_gaps_roadmap": [
    {
      "skill": "SIEM Tools",
      "momentum_score": 0.711,
      "trend": "rising",
      "why_it_matters": "...",
      "resources": [{"name": "...", "url": "...", "time_estimate": "..."}],
      "ai_powered": true
    }
  ]
}
```

---

## AI Disclosure

**AI tools used:** Yes. Claude Code was used for code generation, architectural feedback, and iterating on the dataset design. Gemini 2.5 Flash is used at runtime for resume parsing and roadmap generation.

**Verification approach:** All AI-generated code was tested manually and through automated tests. The synthetic dataset was validated with a script that checks skill frequency distributions and month concentrations match the design constraints. API fallback paths were tested by running the app without an API key to confirm deterministic results.

**Rejected suggestion:** Early in development, AI suggested using SQLite to store job postings and user sessions. I rejected this because the dataset is 70 static records that load in <1ms from a JSON file, and there are no user accounts or persistent state to manage. Adding a database would have meant writing migrations, connection handling, and ORM setup — complexity that adds nothing for a demo and takes time away from the scoring logic and UI, which are the actual point of the project.

---

## Tradeoffs & Prioritization

### What I cut

- **User authentication** — no login, no sessions. The demo flow is paste-and-go.
- **Persistent storage** — no database. Postings load from a flat JSON file at startup.
- **Multi-role comparison** — the app analyzes one target role at a time.
- **Real job board integration** — the dataset is synthetic. No live API calls to LinkedIn, Indeed, etc.

### What I'd build next

1. **Real jobs API integration** — pull from LinkedIn or Indeed to replace synthetic data with live market signals
2. **User profiles** — let users save results and track how their skill gaps close over time
3. **Multi-role comparison** — show gap analysis across 2-3 roles side by side so users can pick the most accessible career path
4. **News and economic signal integration** — incorporate recent tech news, earnings reports, and labor market data to predict which skills will surge in demand, rather than relying solely on historical job postings

### Known limitations

- **Simplified recency model** — `posted_month` (1–12 integer) is a proxy for actual posting dates. Real timestamps would enable rolling-window trend calculations.
- **Synthetic data** — momentum scores reflect patterns I designed into the dataset, not real market conditions. The scoring engine is real; the signal it's processing is illustrative.
- **Plain text only** — resume parsing expects pasted text, not PDF uploads. Adding PDF support would require a parsing library (e.g. PyMuPDF) and OCR for scanned documents.
