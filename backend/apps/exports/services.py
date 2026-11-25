"""PDF export flow with unlock reservation and failure-safe credit handling."""
import logging

from django.core.files.base import ContentFile

from apps.resumes.services import build_render_data
from apps.rewards.services import consume_export_unlock, release_export_unlock, reserve_export_unlock

from .models import PdfExport
from .renderer import render_pdf

logger = logging.getLogger(__name__)


class ExportLocked(Exception):
    pass


class ExportRuntimeError(Exception):
    pass


def export_resume(resume, page_size=None):
    """Export flow per PRD section 10.

    Reserve the unlock, generate the PDF, consume the unlock only on success,
    and release it back to the user on failure.
    """
    if page_size is None:
        from apps.system_settings.models import get_setting

        page_size = get_setting("exports", "page_size_default", "a4")
    unlock = reserve_export_unlock(resume.user)
    if unlock is None:
        raise ExportLocked("No export credit available. Complete the required rewarded ads first.")

    export = PdfExport.objects.create(
        user=resume.user, resume=resume, page_size=page_size, unlock=unlock
    )
    if resume.template_version:
        definition = resume.template_version.definition
    else:
        definition = {"settings": {"page_size": page_size}, "pages": [{"elements": [
            {
                "type": "text", "field": "full_name", "dataSource": "cv",
                "x": 40, "y": 40, "width": 300, "height": 24,
                "textProps": {"size": 18, "weight": "bold"},
            },
        ]}]}

    try:
        pdf_bytes = render_pdf(definition, build_render_data(resume))
        export.file.save(f"cv_{resume.pk}_{export.pk}.pdf", ContentFile(pdf_bytes), save=True)
        export.status = PdfExport.SUCCEEDED
        export.save(update_fields=["file", "status"])
        consume_export_unlock(unlock)
        return export
    except Exception as exc:  # noqa: BLE001
        export.status = PdfExport.FAILED
        export.error = str(exc)
        export.save(update_fields=["status", "error"])
        release_export_unlock(unlock)
        logger.exception("PDF export failed for resume %s", resume.pk)
        raise ExportRuntimeError("PDF generation failed. Your export credit was returned to you.") from exc
