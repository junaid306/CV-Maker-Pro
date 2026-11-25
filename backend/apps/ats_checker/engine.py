"""Rule-based ATS checker. No AI API required for basic analysis.

The score is an estimated compatibility indicator, never a real employer ATS
result or a hiring guarantee. Weighted categories come from admin settings.
"""
import re
from collections import Counter

DEFAULT_WEIGHTS = {
    "contact": 15,
    "summary": 10,
    "experience": 20,
    "education": 15,
    "skills": 15,
    "keywords": 10,
    "formatting": 10,
    "readability": 5,
}

STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "our", "their", "will", "have", "has", "are", "was", "were",
    "that", "this", "from", "into", "about", "who", "whom", "which", "been", "also", "such", "using", "use",
    "role", "job", "work", "company", "team", "years", "year", "strong", "good", "great", "able", "must",
}


def tokenize(text):
    return [t for t in re.findall(r"[a-zA-Z][a-zA-Z\+\#\-\.]{1,}", (text or "").lower())]


def significant_words(text, min_len=3, limit=25):
    counts = Counter(
        t for t in tokenize(text) if len(t) >= min_len and t not in STOPWORDS and not t.isdigit()
    )
    return [word for word, _ in counts.most_common(limit)]


def estimate_readability(text):
    sentences = [s for s in re.split(r"[.!?]+", text or "") if s.strip()]
    words = tokenize(text)
    if not sentences or not words:
        return 0.0, words
    avg_len = len(words) / len(sentences)
    long_ratio = sum(1 for w in words if len(w) > 14) / max(len(words), 1)
    score = 100.0
    score -= min(abs(avg_len - 16) * 3, 60)
    score -= long_ratio * 200
    return max(score, 0.0), words


def analyze_cv(cv_data, sections=None, job_description=None, weights=None):
    """cv_data: plain-text extraction or structured dict from build_render_data()."""
    weights = weights or DEFAULT_WEIGHTS
    findings, suggestions = [], []

    plain_text = _to_plain_text(cv_data, sections)
    words = tokenize(plain_text)

    sections_scores = {}

    contact_fields = ["full_name", "phone", "email"]
    contact_hits = sum(1 for f in contact_fields if (cv_data or {}).get(f))
    sections_scores["contact"] = round(contact_hits / len(contact_fields) * weights["contact"])
    if contact_hits < len(contact_fields):
        missing = [f for f in contact_fields if not (cv_data or {}).get(f)]
        findings.append(f"Contact information incomplete: missing {', '.join(missing)}.")
        suggestions.append("Add all requested contact details (name, phone, email).")

    summary = (cv_data or {}).get("professional_summary") or (cv_data or {}).get("career_objective") or ""
    if summary:
        length = len(summary.split())
        sections_scores["summary"] = weights["summary"] if 25 <= length <= 120 else int(weights["summary"] * 0.6)
        if length < 25:
            findings.append("Professional summary is very short.")
            suggestions.append("Expand your summary to 2-4 sentences.")
    else:
        sections_scores["summary"] = 0
        findings.append("No professional summary or career objective found.")
        suggestions.append("Add a professional summary or career objective at the top.")

    experience = _entries(cv_data, "experience", ["company", "position", "start", "end", "description"])
    sections_scores["experience"] = weights["experience"] if experience else 0
    if not experience:
        findings.append("No work experience entries detected.")
        suggestions.append("Add at least one work experience entry with role and responsibilities.")

    education = _entries(cv_data, "education", ["degree", "institution", "year", "grade"])
    sections_scores["education"] = weights["education"] if education else int(weights["education"] * 0.4)
    if not education:
        findings.append("No education entries detected.")
        suggestions.append("Add your education history.")

    skills = _skill_list(cv_data)
    sections_scores["skills"] = min(round(len(skills) / 8 * weights["skills"]), weights["skills"])
    if len(skills) < 4:
        findings.append("Fewer than 4 skills listed.")
        suggestions.append("List more relevant skills (aim for 8-12).")

    min_letter = 8
    letters_ok = bool(re.search(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", plain_text))
    phone_ok = bool(re.search(r"(\+?\d[\d\-\s()]{7,}\d)", plain_text))
    format_penalty = 0
    if not letters_ok:
        format_penalty += 40
        findings.append("No valid email address found.")
    if not phone_ok:
        format_penalty += 40
        findings.append("No phone number found.")
    if re.search(r"(?i)(please find attached|dear sir|to whom it may concern)", plain_text):
        format_penalty += 20
        suggestions.append("Remove letter-like phrases; use a professional summary instead.")

    custom_words = significant_words(plain_text)
    sections_scores["formatting"] = round(max(weights["formatting"] - format_penalty * weights["formatting"] / 100, 0))
    readability_score, _ = estimate_readability(plain_text)
    sections_scores["readability"] = round(readability_score / 100 * weights["readability"])

    missing_keywords = []
    keyword_score = weights["keywords"]
    if job_description:
        jd_words = significant_words(job_description, limit=30)
        cv_word_set = set(custom_words) | set(words)
        missing_keywords = [w for w in jd_words if w not in cv_word_set][:15]
        coverage = 1 - (len(missing_keywords) / max(len(jd_words), 1))
        keyword_score = round(coverage * weights["keywords"])
    sections_scores["keywords"] = keyword_score

    total = sum(sections_scores.values())
    return {
        "total_score": min(int(round(total)), 100),
        "section_scores": sections_scores,
        "findings": findings,
        "suggestions": suggestions[:10],
        "missing_keywords": missing_keywords,
        "disclaimer": "This score is an estimated ATS compatibility indicator, not an actual employer ATS result or a hiring guarantee.",
    }


def _entries(cv_data, key, fields):
    entries = (cv_data or {}).get(key) or []
    if isinstance(entries, dict):
        entries = entries.get("entries", [])
    valid = []
    for entry in entries or []:
        if isinstance(entry, dict) and any(entry.get(f) for f in fields):
            valid.append(entry)
    return valid


def _skill_list(cv_data):
    skills = (cv_data or {}).get("skills") or []
    if isinstance(skills, dict):
        skills = skills.get("entries", [])
    result = []
    for skill in skills or []:
        if isinstance(skill, dict):
            result.append(skill.get("name", ""))
        elif isinstance(skill, str):
            result.append(skill)
    return [s for s in result if s]


def _to_plain_text(cv_data, sections=None):
    if isinstance(cv_data, str):
        return cv_data
    parts = [str(v) for v in (cv_data or {}).values() if isinstance(v, str)]

    def render(entry, fields_order):
        out = []
        for field, value in entry.items():
            if isinstance(value, str):
                out.append(value)
        return " ".join(out)

    for key in ("experience", "education", "projects", "certifications", "achievements"):
        entries = _entries(cv_data, key, ["description"])
        for entry in entries:
            parts.append(render(entry, None))
    for skill in _skill_list(cv_data):
        parts.append(skill)
    return " ".join(parts)
