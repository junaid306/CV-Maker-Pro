"""Resume business logic: snapshots, duplicate, restore, render-time merge."""
from copy import deepcopy

from django.db import transaction
from django.utils import timezone

CV_FIELDS = {
    "full_name",
    "phone",
    "email",
    "address",
    "career_objective",
    "professional_summary",
    "profile_photo",
}


@transaction.atomic
def snapshot_resume(resume, note=""):
    sections = list(resume.sections.all())
    return resume.versions.create(
        snapshot={
            "title": resume.title,
            "template_id": resume.template_id,
            "template_version_id": resume.template_version_id,
            "data": resume.data,
            "sections": [
                {"key": s.key, "title": s.title, "order": s.order, "data": s.data} for s in sections
            ],
        },
        note=note,
    )


@transaction.atomic
def duplicate_resume(resume, title=None):
    clone = Resume.objects.create(
        user=resume.user,
        template=resume.template,
        template_version=resume.template_version,
        title=title or f"{resume.title} (copy)",
        data=deepcopy(resume.data),
    )
    for section in resume.sections.all():
        ResumeSection.objects.create(
            resume=clone, key=section.key, title=section.title, order=section.order, data=deepcopy(section.data)
        )
    return clone


@transaction.atomic
def restore_version(resume, version):
    snap = version.snapshot
    resume.title = snap.get("title", resume.title)
    if snap.get("template_id"):
        resume.template_id = snap.get("template_id")
        resume.template_version_id = snap.get("template_version_id")
    resume.data = snap.get("data", {})
    resume.save(update_fields=["title", "template_id", "template_version_id", "data", "updated_at"])
    for section in resume.sections.all():
        section.delete()
    for order, section in enumerate(snap.get("sections", [])):
        ResumeSection.objects.create(
            resume=resume, key=section.get("key", "custom"), title=section.get("title", ""),
            order=section.get("order", order), data=section.get("data", {}),
        )
    return resume


def build_render_data(resume):
    """Map CV data onto template element fields for rendering/export."""
    data = resume.data or {}
    out = {key: data.get(key, "") for key in CV_FIELDS if key in data}
    for section in resume.sections.all():
        key = section.key
        entries = section.data.get("entries", []) if isinstance(section.data, dict) else []
        out.setdefault(key, entries if entries else section.data)
    return out
