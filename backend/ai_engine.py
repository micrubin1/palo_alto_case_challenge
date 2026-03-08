import json
import logging
import os
import re

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        _client = genai.GenerativeModel("gemini-2.5-flash")
    return _client


# ---------------------------------------------------------------------------
# Resume parsing
# ---------------------------------------------------------------------------

COMMON_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust",
    "Ruby", "Perl", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL",
    "Bash Scripting", "PowerShell", "HTML", "CSS",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
    "Jenkins", "Git", "GitHub Actions", "CI/CD Pipelines", "Linux Administration",
    "React", "Angular", "Vue", "Node.js", "Flask", "Django", "Spring Boot",
    "REST APIs", "GraphQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
    "SIEM Tools", "Splunk", "Wireshark", "Nmap", "Metasploit",
    "Zero Trust Architecture", "Cloud Security Posture Management (CSPM)",
    "AI/ML Security", "Penetration Testing", "Incident Response",
    "Network Security", "IAM", "Encryption Protocols", "Compliance Frameworks",
    "OWASP", "ITIL Certification", "CompTIA Security+",
    "AWS Certified Cloud Practitioner", "TCP/IP", "DNS",
]


def _fallback_parse(resume_text: str) -> list[str]:
    logger.warning("AI parse failed, using keyword fallback")
    text_lower = resume_text.lower()
    return [s for s in COMMON_SKILLS if s.lower() in text_lower]


def parse_resume(resume_text: str) -> list[str]:
    try:
        model = _get_client()
        response = model.generate_content(
            [
                "You are a resume parser. Extract only technical skills, tools, "
                "technologies, and certifications. Return a JSON array of strings "
                "only. No explanation, no markdown, no preamble.",
                resume_text,
            ]
        )
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        skills = json.loads(raw)
        if isinstance(skills, list) and all(isinstance(s, str) for s in skills):
            return skills
        return _fallback_parse(resume_text)
    except Exception as exc:
        logger.warning("parse_resume error: %s", exc)
        return _fallback_parse(resume_text)


# ---------------------------------------------------------------------------
# Roadmap generation
# ---------------------------------------------------------------------------

FALLBACK_ROADMAP: dict[str, dict] = {
    "Kubernetes": {
        "why_it_matters": "Kubernetes is the industry standard for container orchestration in cloud security environments.",
        "resources": [
            {"name": "Kubernetes Basics – official tutorial", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "time_estimate": "6 hours"},
            {"name": "KodeKloud Free Kubernetes Course", "url": "https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners/", "time_estimate": "8 hours"},
        ],
    },
    "Zero Trust Architecture": {
        "why_it_matters": "Zero Trust is replacing perimeter-based security as the default model for enterprise networks.",
        "resources": [
            {"name": "NIST SP 800-207 Zero Trust Architecture", "url": "https://csrc.nist.gov/publications/detail/sp/800-207/final", "time_estimate": "3 hours"},
            {"name": "Google BeyondCorp papers", "url": "https://cloud.google.com/beyondcorp", "time_estimate": "4 hours"},
        ],
    },
    "SIEM Tools": {
        "why_it_matters": "SIEM platforms are central to threat detection and incident response in SOC environments.",
        "resources": [
            {"name": "Splunk Free Training", "url": "https://www.splunk.com/en_us/training/free-courses.html", "time_estimate": "10 hours"},
            {"name": "Elastic SIEM Getting Started", "url": "https://www.elastic.co/security", "time_estimate": "6 hours"},
        ],
    },
    "Cloud Security Posture Management (CSPM)": {
        "why_it_matters": "CSPM tools continuously monitor cloud infrastructure for misconfigurations and compliance violations.",
        "resources": [
            {"name": "AWS Security Hub Workshop", "url": "https://catalog.workshops.aws/security-hub/", "time_estimate": "4 hours"},
            {"name": "Prisma Cloud Fundamentals (Palo Alto Networks)", "url": "https://www.paloaltonetworks.com/prisma/cloud", "time_estimate": "5 hours"},
        ],
    },
    "AI/ML Security": {
        "why_it_matters": "As AI adoption grows, securing ML pipelines and defending against adversarial attacks is a critical emerging skill.",
        "resources": [
            {"name": "OWASP Machine Learning Security Top 10", "url": "https://owasp.org/www-project-machine-learning-security-top-10/", "time_estimate": "3 hours"},
            {"name": "Google Secure AI Framework (SAIF)", "url": "https://safety.google/cybersecurity-advancements/saif/", "time_estimate": "2 hours"},
        ],
    },
    "Incident Response": {
        "why_it_matters": "Incident response skills are essential for containing and recovering from security breaches.",
        "resources": [
            {"name": "SANS Incident Handler's Handbook", "url": "https://www.sans.org/white-papers/33901/", "time_estimate": "4 hours"},
            {"name": "Cybrary Incident Response Free Course", "url": "https://www.cybrary.it", "time_estimate": "6 hours"},
        ],
    },
}


def _fallback_roadmap(skill: str, target_role: str) -> dict:
    if skill in FALLBACK_ROADMAP:
        item = dict(FALLBACK_ROADMAP[skill])
        item["ai_powered"] = False
        return item
    return {
        "why_it_matters": f"{skill} is frequently required for {target_role} roles.",
        "resources": [
            {
                "name": f"Search: '{skill} tutorial for beginners'",
                "url": "https://www.google.com",
                "time_estimate": "varies",
            }
        ],
        "ai_powered": False,
    }


def generate_roadmap_item(
    skill: str, momentum_score: float, target_role: str
) -> dict:
    try:
        model = _get_client()
        prompt = (
            f"You are a technical career coach. The candidate is targeting the role "
            f"of {target_role} and is missing the skill: {skill} (market demand score: "
            f"{momentum_score:.2f} out of 1.0). Suggest exactly 2 specific learning "
            f'resources (free preferred). Be concise. Return JSON only in this format: '
            f'{{"why_it_matters": "one sentence", "resources": '
            f'[{{"name": "resource name", "url": "url or search term", '
            f'"time_estimate": "e.g. 4 hours"}}]}}'
        )
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        item = json.loads(raw)
        if "why_it_matters" in item and "resources" in item:
            item["ai_powered"] = True
            return item
        return _fallback_roadmap(skill, target_role)
    except Exception as exc:
        logger.warning("generate_roadmap_item error for %s: %s", skill, exc)
        return _fallback_roadmap(skill, target_role)
