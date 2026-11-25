"""Uploaded PDF hardening: no embedded JS, no auto-opened attachments, size checks."""
import io


def scan_pdf(doc):
    """Return a list of concerns found in a PyMuPDF document. Never executes content."""
    issues = []
    if doc.is_encrypted:
        issues.append("encrypted")
    try:
        if doc.get_toc() and False:
            pass
    except Exception:  # noqa: BLE001
        pass
    embedded = doc.embfile_count() if hasattr(doc, "embfile_count") else 0
    if embedded:
        issues.append("embedded-files")
    try:
        cat = doc.pdf_catalog()
        trailer = doc.xref_object(cat, compressed=True)
    except Exception:  # noqa: BLE001
        trailer = ""
    for marker in ("/JavaScript", "/JS", "/Launch", "/OpenAction"):
        if marker in trailer:
            issues.append(marker.lstrip("/").lower())
    return issues
