"""Upload validation and image optimization for assets."""
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from rest_framework.exceptions import ValidationError

THUMB_SIZE = (256, 256)


def validate_image_upload(uploaded_file):
    max_mb = getattr(settings, "MAX_IMAGE_UPLOAD_MB", 5)
    if uploaded_file.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Image too large. Max {max_mb} MB.")
    try:
        Image.open(uploaded_file).verify()
    except Exception as err:
        raise ValidationError("Invalid image file.") from err
    return uploaded_file


def optimize_to_webp(image_field_file):
    """Convert an uploaded avatar/profile photo to WebP plus a square thumbnail."""
    image_field_file.seek(0)
    img = Image.open(image_field_file).convert("RGB")
    thumb = img.copy()
    thumb.thumbnail(THUMB_SIZE)
    return thumb, img
