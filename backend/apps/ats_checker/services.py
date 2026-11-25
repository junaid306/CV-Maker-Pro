"""ATS analysis orchestration."""
from django.core.exceptions import ValidationError

from apps.resumes.services import build_render_data

from .engine import analyze_cv
from .models import AtsAnalysis


def analyze_resume(resume, job_description=None, weights=None):
    if resume is None:
        raise ValidationError("A resume is required.")
    data = build_render_data(resume)
    result = analyze_cv(data, sections=None, job_description=job_description, weights=weights)
    return AtsAnalysis.objects.create(
        user=resume.user, resume=resume,
        total_score=result["total_score"], section_scores=result["section_scores"],
        findings=result["findings"], suggestions=result["suggestions"],
        missing_keywords=result["missing_keywords"], used_ai=False,
    )


def analyze_text(user, text, job_description=None):
    result = analyze_cv(text, job_description=job_description)
    return AtsAnalysis.objects.create(
        user=user, total_score=result["total_score"], section_scores=result["section_scores"],
        findings=result["findings"], suggestions=result["suggestions"],
        missing_keywords=result["missing_keywords"], used_ai=False,
    )
