"""Template publishing and query services."""
from django.db import transaction
from django.utils import timezone

from .models import Template, TemplateVersion
from .schema import validate_template_json


@transaction.atomic
def save_template_version(template, definition, publish=False, user=None):
    """Validate, normalize and store a new immutable template version."""
    ok, normalized, errors = validate_template_json(definition)
    if not ok:
        raise ValueError("; ".join(errors))
    next_no = template.versions.count() + 1
    version = TemplateVersion.objects.create(
        template=template,
        version_no=next_no,
        definition=normalized,
        published_at=timezone.now() if publish else None,
    )
    template.current_version = version
    if publish:
        template.status = Template.STATUS_PUBLISHED
    template.save(update_fields=["current_version", "status", "updated_at"])
    return version


@transaction.atomic
def publish_template(template, user=None):
    version = template.current_version
    if not version:
        raise ValueError("Template has no version to publish.")
    version.published_at = version.published_at or timezone.now()
    version.save(update_fields=["published_at"])
    template.status = Template.STATUS_PUBLISHED
    template.save(update_fields=["status", "updated_at"])
    return template
