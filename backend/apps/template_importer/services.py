"""Import job orchestration: validate -> convert -> previews -> review -> publish."""
import logging

from django.conf import settings
from django.core.files.base import ContentFile

from apps.exports.renderer import render_preview_png
from apps.template_importer.converter import convert_pdf_to_template, validate_source_pdf
from apps.templates_manager.services import save_template_version

from .models import ConversionElement, TemplateImportJob

logger = logging.getLogger(__name__)


class ImportValidationError(ValueError):
    pass


def process_import_job(job):
    """Run the full pipeline synchronously (swap to Celery for production volume)."""
    job.status = TemplateImportJob.STATUS_PROCESSING
    job.save(update_fields=["status"])
    job.source_pdf.open("rb")
    pdf_bytes = job.source_pdf.read()
    job.source_pdf.close()
    doc = None
    try:
        max_mb = getattr(settings, "MAX_PDF_UPLOAD_MB", 10)
        max_pages = getattr(settings, "MAX_PDF_PAGES", 10)
        doc, warnings = validate_source_pdf(pdf_bytes, max_mb=max_mb, max_pages=max_pages)
        definition, convert_warnings, pages = convert_pdf_to_template(doc)
        warnings.extend(convert_warnings)
        name = job.name or "Imported template"
        from apps.templates_manager.models import Template, TemplateCategory

        category, _ = TemplateCategory.objects.get_or_create(
            slug="imported", defaults={"name": "Imported", "order": 99}
        )
        template = Template.objects.create(
            name=name, category=category, status=Template.STATUS_DRAFT, created_by=job.uploaded_by
        )
        version = save_template_version(template, definition, publish=False, user=job.uploaded_by)
        for page in pages:
            job.pages.create(
                page_no=page["page_no"], width=page["width"], height=page["height"],
                is_scanned=page["is_scanned"], extracted_text=(page.get("text") or "")[:20000],
            )
        preview = render_preview_png(definition, {})
        preview_name = f"job_{job.pk}_preview.png"
        job.preview_png.save(preview_name, ContentFile(_png_bytes(preview)), save=True)
        job.status = TemplateImportJob.STATUS_REVIEW
        job.warnings = warnings
        job.generated_template = version
        job.published_template = template
        job.save(update_fields=["status", "warnings", "generated_template", "published_template", "preview_png"])
    except Exception as exc:  # noqa: BLE001
        logger.exception("PDF import failed for job %s", job.pk)
        job.status = TemplateImportJob.STATUS_FAILED
        job.errors = [str(exc)]
        job.save(update_fields=["status", "errors"])
        raise
    finally:
        if doc is not None:
            doc.close()
    return job


def approve_and_publish(job, user):
    from apps.templates_manager.services import publish_template

    if job.status != TemplateImportJob.STATUS_REVIEW or not job.generated_template:
        raise ImportValidationError("Job is not ready for approval.")
    template = job.published_template or job.generated_template.template
    publish_template(template, user=user)
    job.status = TemplateImportJob.STATUS_PUBLISHED
    job.save(update_fields=["status"])
    return template


def _png_bytes(pil_image):
    out = __import__("io").BytesIO()
    pil_image.save(out, format="PNG")
    out.seek(0)
    return out.getvalue()
