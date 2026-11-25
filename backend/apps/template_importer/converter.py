"""PDF-to-JSON conversion pipeline (PyMuPDF + pdfplumber), inside Django.

Known limitations surfaced to the admin: OCR-only pages, custom fonts and
complex graphics need manual correction; confidence warnings are recorded.
"""
import io

import fitz  # PyMuPDF

from apps.templates_manager.schema import SCHEMA_VERSION


def validate_source_pdf(pdf_bytes, max_mb=10, max_pages=10):
    size_mb = len(pdf_bytes) / (1024 * 1024)
    if size_mb > max_mb:
        raise ValueError(f"PDF exceeds {max_mb} MB limit.")
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # noqa: BLE001
        from apps.template_importer.security import looks_like_encrypted_or_malformed

        raise ValueError("Invalid or corrupted PDF file.") from exc

    from apps.template_importer.security import scan_pdf

    issues = scan_pdf(doc)
    if doc.page_count > max_pages:
        raise ValueError(f"PDF has {doc.page_count} pages; max is {max_pages}.")
    if doc.needs_pass:
        raise ValueError("Password-protected PDFs are not supported.")
    warnings = []
    if issues:
        warnings.append(f"Potentially unsafe content ignored: {', '.join(issues)}")
    warnings.extend(["Scanned or image-only pages may need OCR and manual correction."])
    return doc, warnings


def detect_page_size(doc):
    page = doc.load_page(0)
    rect = page.rect
    if rect.width <= rect.height:
        return "a4", rect
    return "a4-landscape", rect


SECTION_HEADINGS = {
    "professional summary": "professional_summary",
    "summary": "professional_summary",
    "objective": "career_objective",
    "career objective": "career_objective",
    "experience": "experience",
    "work experience": "experience",
    "employment": "experience",
    "education": "education",
    "skills": "skills",
    "projects": "projects",
    "certifications": "certifications",
    "languages": "languages",
    "achievements": "achievements",
    "references": "references",
}


def convert_pdf_to_template(doc):
    """Extract text blocks with coordinates and emit a template JSON v1."""
    warnings = []
    pages_out = []
    imported_pages = []
    for page_no in range(doc.page_count):
        page = doc.load_page(page_no)
        rect = page.rect
        text = page.get_text("text")
        is_scanned = bool(page.get_images(full=True)) and len(text.strip()) < 20
        imported_pages.append({"page_no": page_no + 1, "width": rect.width, "height": rect.height, "is_scanned": is_scanned, "text": text})
        if is_scanned:
            warnings.append(f"Page {page_no + 1} looks scanned; text needs OCR/manual correction.")
        elements = []
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if not line_text:
                    continue
                spans = line.get("spans", [])
                first = spans[0] if spans else {}
                size = round(float(first.get("size", 11)), 1)
                weight = "bold" if (first.get("flags", 0) & 16) else "normal"
                color = _int_color_to_hex(first.get("color", 0))
                text_key = "static"
                field = None
                heading = SECTION_HEADINGS.get(line_text.strip().lower())
                if heading:
                    text_key = "static"
                field = _guess_field(line_text, heading)
                elements.append({
                    "type": "text",
                    "x": round(line["bbox"][0], 2),
                    "y": round(line["bbox"][1], 2),
                    "width": round(line["bbox"][2] - line["bbox"][0], 2),
                    "height": round(line["bbox"][3] - line["bbox"][1], 2),
                    "dataSource": "cv" if field else "static",
                    "field": field,
                    "text": line_text,
                    "textProps": {"size": size, "weight": weight, "color": color},
                    "z": len(elements),
                })
        # images: preserve placeholder only; never extract sample photos.
        for image_info in page.get_images(full=True):
            xref = image_info[0]
            try:
                rects = page.get_image_rects(xref)
            except Exception:  # noqa: BLE001
                continue
            for rect2 in rects:
                elements.append({
                    "type": "image",
                    "x": round(rect2.x0, 2), "y": round(rect2.y0, 2),
                    "width": round(rect2.width, 2), "height": round(rect2.height, 2),
                    "dataSource": "photo",
                    "field": "profile_photo",
                    "defaultImage": "avatar_01",
                    "allowUserUpload": True,
                    "shape": "circle" if abs(rect2.width - rect2.height) < 4 else "rect",
                    "z": len(elements),
                })
                warnings.append("Image kept as a photo placeholder (shared avatar), sample image not extracted.")
        page_out = {"id": f"page_{page_no + 1}", "background": "#FFFFFF", "elements": elements}
        pages_out.append(page_out)

    size_key, rect = detect_page_size(doc)
    page_w, page_h = fitz.paper_size("a4") if not size_key.endswith("landscape") else (fitz.paper_size("a4")[1], fitz.paper_size("a4")[0])
    for page in pages_out:
        for element in page["elements"]:
            if element["type"] == "text":
                element["width"] = min(element["width"], page_w - 2 * 36)
    definition = {
        "schema_version": SCHEMA_VERSION,
        "settings": {"page_size": "a4" if size_key == "a4" else "a4", "margin": 36},
        "pages": pages_out,
    }
    return definition, warnings, imported_pages


def _guess_field(line_text, heading):
    lowered = line_text.strip().lower()
    if heading:
        return None
    if "@" in line_text:
        return "email"
    if "@" not in lowered and lowered.startswith(("+88", "+", "01")) and any(ch.isdigit() for ch in line_text):
        return "phone"
    return None


def _int_color_to_hex(color_int):
    r = (color_int >> 16) & 255
    g = (color_int >> 8) & 255
    b = color_int & 255
    return f"#{r:02x}{g:02x}{b:02x}"
