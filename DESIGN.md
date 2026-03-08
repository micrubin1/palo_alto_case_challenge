# Design Documentation

## Overview

Skill Futures is a career navigator web app that helps job seekers prioritize which skill gaps to close first. Rather than treating all missing skills equally, it ranks gaps using a **Demand Momentum Score** derived from job posting frequency and recency trends.

The core insight: a skill appearing in 65% of recent postings with growing demand is a better investment of learning time than a skill appearing in 40% of older postings with declining demand.

---

## Architecture

```
┌─────────────────────┐       POST /analyze       ┌──────────────────────────┐
│                     │ ────────────────────────▶  │     FastAPI Backend      │
│   Browser (SPA)     │                            │                          │
│   index.html        │  ◀────────────────────────  │  ┌──────────────────┐   │
│   Tailwind + Chart.js│       JSON response        │  │  ai_engine.py    │   │
└─────────────────────┘                            │  │  (Gemini API +   │   │
                                                   │  │   fallbacks)     │   │
                                                   │  └──────────────────┘   │
                                                   │  ┌──────────────────┐   │
                                                   │  │  scorer.py       │   │
                                                   │  │  (momentum       │   │
                                                   │  │   scoring)       │   │
                                                   │  └──────────────────┘   │
                                                   │  ┌──────────────────┐   │
                                                   │  │  data_loader.py  │──▶ data/job_postings.json
                                                   │  └──────────────────┘   │
                                                   └──────────────────────────┘
```

### Request Flow

1. User pastes resume text and selects a target role in the browser
2. Frontend sends `POST /analyze` with `{resume_text, target_role}` to the backend
3. `ai_engine.parse_resume()` extracts skills via Gemini (or keyword fallback)
4. `scorer.get_gaps()` filters postings by role, identifies missing skills, computes momentum scores
5. `ai_engine.generate_roadmap_item()` generates learning resources for the top 3 gaps
6. Backend returns extracted skills, all ranked gaps, and top 3 roadmap items
7. Frontend renders the dashboard (Chart.js bar chart) and roadmap cards

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python + FastAPI | Fast to build, async-capable, automatic OpenAPI docs, Pydantic validation for request/response models |
| **AI** | Google Gemini 2.5 Flash via `google-generativeai` SDK | Free tier available, low latency (~1s), sufficient for structured JSON extraction tasks |
| **Frontend** | Single `index.html` with vanilla JS | Zero build step, no node_modules, trivially deployable — appropriate for a demo/take-home scope |
| **Styling** | Tailwind CSS (CDN) | Utility-first CSS without a build pipeline, fast iteration on layout |
| **Charting** | Chart.js (CDN) | Lightweight, well-documented, horizontal bar charts work well for ranked skill data |
| **Data** | Static JSON file (70 synthetic job postings) | No database overhead, loads in <1ms, version-controlled alongside code |
| **Tests** | pytest | Standard Python testing, minimal setup, fast execution |

---

## Data Design

### Synthetic Dataset (70 postings)

The dataset was designed to make the scoring model produce interesting, demonstrable results:

- **High-momentum skills** (Kubernetes, Zero Trust Architecture, Python, SIEM Tools, CSPM, AI/ML Security): Appear in 60–76% of postings, concentrated in months 8–12. These score highest because they are both frequent and recent.
- **Declining skills** (Perl, On-Premise Firewall Management, CVS Version Control, ITIL Certification): Appear in 40–44% of postings, concentrated in months 1–5. High frequency keeps them visible, but low recency drags their momentum score down.
- **25+ other skills** distributed naturally across postings to provide realistic variety.

This two-tier design ensures the demo clearly shows momentum scoring working as intended — rising skills rank above declining ones even when raw frequency counts are comparable.

### Sample Resume

Alex Chen is a fictional CS new-grad with solid fundamentals (Python, AWS, Git, Docker, networking) but deliberately missing the high-momentum skills (Kubernetes, CSPM, Zero Trust, AI/ML Security, SIEM Tools). This guarantees the demo produces meaningful, visually clear gap analysis.

---

## Scoring Model

### Demand Momentum Score

```
momentum_score = (0.6 × frequency_score) + (0.4 × recency_score)
```

- **frequency_score** = (number of postings containing skill) / (total postings)
- **recency_score** = average(posted_month for postings with this skill) / 12

### Why 60/40 Weighting

Frequency is weighted higher because established demand matters more than trend direction for career investment decisions. A skill required by 70% of employers is worth learning even if growth has plateaued. Pure recency weighting would over-promote niche skills that appeared in a handful of recent postings.

The 40% recency component still meaningfully differentiates: two skills with identical frequency but different recency (one concentrated in recent months, one in older months) will produce visibly different scores.

### Trend Labels

Derived from the recency score of each skill:
- **Rising** (recency > 0.6): Demand concentrated in recent months
- **Stable** (recency 0.4–0.6): Demand spread evenly across the year
- **Declining** (recency < 0.4): Demand concentrated in earlier months

---

## AI Integration & Fallback Architecture

### Two AI-Powered Functions

| Function | AI Path | Fallback Path |
|----------|---------|---------------|
| `parse_resume()` | Gemini extracts skills as JSON array | Case-insensitive keyword match against 60 common tech skills |
| `generate_roadmap_item()` | Gemini generates "why it matters" + 2 resources with time estimates | Curated dictionary for 6 high-momentum skills; generic search template for others |

### Why Fallbacks Matter

1. **Reliability**: The app returns useful results even when the API key is missing, quota is exhausted, or the network is down. During development, we hit Gemini free-tier quota limits — the fallback layer meant the app was always functional.
2. **Responsible AI**: Every response includes an `ai_powered: true/false` flag per roadmap item. The frontend displays "AI-powered" or "Rule-based" labels so users know the provenance of each recommendation. The core gap analysis (`scorer.get_gaps()`) is entirely deterministic with no AI dependency.

### Gemini Prompt Design

- **Resume parsing**: System instruction constrains output to a JSON array of strings only — no explanation, no markdown. Response is stripped of any code fences before parsing.
- **Roadmap generation**: Prompt specifies exact JSON schema, includes the skill's momentum score for context, and requests exactly 2 free resources. Structured output reduces post-processing.

---

## Future Enhancements

### Near-Term

- **Real job board integration** — Replace synthetic data with live postings from LinkedIn, Indeed, or similar APIs to produce real market momentum scores
- **User profiles and progress tracking** — Let users save analyses, mark skills as "learning" or "acquired", and track how their gap profile changes over time
- **Multi-role comparison** — Analyze gaps across 2–3 roles simultaneously so users can identify which career path has the most accessible entry point
- **News and economic signal integration** — Incorporate tech industry news, earnings reports, and labor market data to predict which skills will surge in demand, rather than relying solely on historical job posting patterns

### Longer-Term

- **PDF resume upload** — Add a parsing layer (e.g. PyMuPDF) to accept uploaded PDFs instead of requiring pasted text
- **Personalized time estimates** — Factor in the user's existing adjacent skills to estimate realistic learning time (e.g., someone who knows Docker will learn Kubernetes faster)
- **Team/cohort mode** — Let hiring managers or bootcamp instructors analyze skill gaps across a group of candidates to design targeted training programs
- **Real-time momentum dashboard** — A public-facing page showing skill demand trends over time, updated weekly from live job data

---

## Known Limitations

- **Simplified recency model**: `posted_month` is an integer 1–12, not a real timestamp. This prevents rolling-window or decay-based trend calculations.
- **Synthetic data**: Momentum scores reflect designed patterns, not real market conditions. The scoring engine is production-ready; the data feeding it is illustrative.
- **Keyword fallback noise**: The fallback resume parser uses substring matching, which can produce false positives for short skill names (e.g., "C" and "R" match inside other words). The AI path does not have this issue.
- **No caching**: Each `/analyze` call makes up to 4 Gemini API calls (1 parse + 3 roadmap items). Adding a response cache keyed on resume hash + role would reduce latency and API usage for repeated analyses.
