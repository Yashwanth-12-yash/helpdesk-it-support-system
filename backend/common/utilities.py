import os
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_uploaded_file(uploaded_file):
    """Validate file extension and maximum allowed file size."""
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(
            f"File size exceeds the maximum limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    _, ext = os.path.splitext(uploaded_file.name)
    ext = ext.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(settings.ALLOWED_UPLOAD_EXTENSIONS))
        raise ValidationError(f"Unsupported file type '{ext}'. Allowed types: {allowed}")


def generate_attachment_upload_path(instance, filename):
    """Store uploaded files under randomized UUID names to prevent path traversal."""
    _, ext = os.path.splitext(filename)
    ticket_id = getattr(instance, "ticket_id", "general")
    return f"tickets/{ticket_id}/{uuid.uuid4().hex}{ext.lower()}"


def get_client_ip(request):
    """Extract client IP address safely from headers or REMOTE_ADDR."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
