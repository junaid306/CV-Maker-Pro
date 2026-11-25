"""Server-side PDF renderer driven by the versioned template JSON schema.

This is the same rendering contract the Flutter app follows (schema v1.0),
so preview and export stay consistent.
"""
import io

from PIL import Image, ImageDraw
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from apps.templates_manager.schema import page_dimensions

PAGE_SIZES_PT = {"a4": (595.28, 841.89), "letter": (612, 792)}


def render_pdf(definition, render_data, user_photo=None):
    """Build a text-selectable PDF from a template definition.

    render_data maps template field names to strings/lists (see
    resumes.services.build_render_data). Returns PDF bytes.
    """
    page_size = (definition.get("settings", {}) or {}).get("page_size", "a4")
    width, height = PAGE_SIZES_PT.get(page_size, PAGE_SIZES_PT["a4"])
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    for page in definition.get("pages", []):
        background = page.get("background")
        if background and background.lower() not in ("#ffffff", "#fff", "white"):
            pdf.setFillColor(HexColor(_safe_color(background)))
            pdf.rect(0, 0, width, height, stroke=0, fill=1)
        for element in sorted(page.get("elements", []), key=lambda e: e.get("z", 0)):
            _draw_element(pdf, element, render_data, height, user_photo)
        pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def render_preview_png(definition, render_data, width_px=700, user_photo=None):
    """Raster preview of the first page, rendered from the JSON (not the source PDF)."""
    import math

    page_size = (definition.get("settings", {}) or {}).get("page_size", "a4")
    pw, ph = PAGE_SIZES_PT.get(page_size, PAGE_SIZES_PT["a4"])
    scale = width_px / pw
    img = Image.new("RGB", (int(pw * scale), int(ph * scale)), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    page = (definition.get("pages") or [{}])[0]
    img.paste(
        Image.new("RGB", img.size, _safe_color(page.get("background", "#FFFFFF"))), (0, 0)
    )
    for element in sorted(page.get("elements", []), key=lambda e: e.get("z", 0)):
        etype = element.get("type")
        x, y = element.get("x", 0) * scale, element.get("y", 0) * scale
        w, h = element.get("width", 0) * scale, element.get("height", 0) * scale
        if etype == "rect":
            draw.rectangle([x, y, x + w, y + h], fill=_safe_color(element.get("fill", "#FFFFFF")),
                           outline=_safe_color(element.get("stroke", "#111827")))
        elif etype == "line":
            vertical = w <= max(2, h * 0.05)
            if vertical:
                draw.line([x + w / 2, y, x + w / 2, y + h], fill=_safe_color(element.get("stroke", "#111827")), width=max(1, int(w)))
            else:
                draw.line([x, y + h / 2, x + w, y + h / 2], fill=_safe_color(element.get("stroke", "#111827")), width=max(1, int(h)))
        elif etype == "ellipse":
            draw.ellipse([x, y, x + w, y + h], fill=_safe_color(element.get("fill", "#FFFFFF")),
                         outline=_safe_color(element.get("stroke", "#111827")))
        elif etype == "image":
            draw.rectangle([x, y, x + w, y + h], outline="#9CA3AF")
        elif etype == "text":
            value = _resolve_text(element, render_data)
            props = element.get("textProps", {})
            font = _load_font(props)
            color = _safe_color(props.get("color", "#111827"))
            _draw_wrapped(draw, value, x, y, w, h, font, color, scale)
    return img


def _resolve_text(element, render_data):
    text = element.get("text", "")
    field = element.get("field")
    if element.get("dataSource") == "cv" and field and render_data:
        value = render_data.get(field, "")
        if isinstance(value, list):
            texts = []
            for entry in value:
                if isinstance(entry, dict):
                    texts.append(" • ".join(str(v) for v in entry.values() if v))
                else:
                    texts.append(str(entry))
            value = "\n".join(texts)
        if field == "profile_photo":
            return text
        text = value if value else text
    return text


def _draw_element(pdf, element, render_data, page_height, user_photo):
    etype = element.get("type")
    x, y = float(element.get("x", 0)), float(element.get("y", 0))
    w, h = float(element.get("width", 0)), float(element.get("height", 0))
    y_pdf = page_height - y  # convert top-left origin
    if etype == "rect":
        pdf.setFillColor(HexColor(_safe_color(element.get("fill", "#FFFFFF"))))
        pdf.setStrokeColor(HexColor(_safe_color(element.get("stroke", "#111827"))))
        pdf.rect(x, y_pdf - h, w, h, stroke=bool(element.get("stroke")), fill=bool(element.get("fill")))
    elif etype == "ellipse":
        pdf.setFillColor(HexColor(_safe_color(element.get("fill", "#FFFFFF"))))
        pdf.ellipse(x, y_pdf - h, x + w, y_pdf, stroke=0, fill=1)
    elif etype == "line":
        pdf.setStrokeColor(HexColor(_safe_color(element.get("stroke", "#111827"))))
        pdf.setLineWidth(float(element.get("strokeWidth", 1)))
        vertical = w <= max(2, h * 0.05)
        if vertical:
            pdf.line(x + w / 2, y_pdf, x + w / 2, y_pdf - h)
        else:
            pdf.line(x, y_pdf - h / 2, x + w, y_pdf - h / 2)
    elif etype == "image":
        image = user_photo if (user_photo and element.get("allowUserUpload")) else None
        if image is not None:
            if element.get("shape") == "circle":
                pdf.saveState()
                path = pdf.beginPath()
                path.circle(x + w / 2, y_pdf - h / 2, min(w, h) / 2)
                pdf.clipPath(path, stroke=0)
                pdf.drawImage(image, x + (w - min(w, h)) / 2, y_pdf - h + (h - min(w, h)) / 2,
                              width=min(w, h), height=min(w, h), mask="auto")
                pdf.restoreState()
            else:
                pdf.drawImage(image, x, y_pdf - h, width=w, height=h, mask="auto")
        elif element.get("shape") == "circle":
            pdf.setStrokeColor(HexColor("#9CA3AF"))
            pdf.circle(x + w / 2, y_pdf - h / 2, min(w, h) / 2, stroke=1, fill=0)
    elif etype == "text":
        value = _resolve_text(element, render_data)
        if not value:
            return
        props = element.get("textProps", {})
        font_name = _pdf_font(props)
        font_size = float(props.get("size", 11))
        color = HexColor(_safe_color(props.get("color", "#111827")))
        pdf.setFont(font_name, font_size)
        pdf.setFillColor(color)
        align = props.get("align", "left")
        line_height = float(props.get("line_height", 1.3)) * font_size
        max_width = w
        wrapped = _wrap_text(value, font_name, font_size, max_width)
        cursor_y = y_pdf - font_size
        for line in wrapped:
            if cursor_y < y_pdf - h - font_size:
                break
            if align == "center":
                pdf.drawCentredString(x + w / 2, cursor_y, line)
            elif align == "right":
                pdf.drawRightString(x + w, cursor_y, line)
            else:
                pdf.drawString(x, cursor_y, line)
            cursor_y -= line_height


HELVETICA_MAP = {
    "bold": ("Helvetica-Bold", None),
}


def _pdf_font(props):
    weight = str(props.get("weight", "normal")).lower()
    family = "Helvetica"
    italic = str(props.get("style", "")).lower() in ("italic", "oblique")
    bold = weight in ("bold", "700", "800", "900", "600")
    if bold and italic:
        return "Helvetica-BoldOblique"
    if bold:
        return "Helvetica-Bold"
    if italic:
        return "Helvetica-Oblique"
    return family


def _wrap_text(value, font_name, font_size, max_width):
    from reportlab.pdfbase.pdfmetrics import stringWidth

    lines = []
    for raw_line in str(value).split("\n"):
        words = raw_line.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def _safe_color(value):
    value = str(value or "#111827").strip()
    if value.startswith("#") and len(value) in (4, 7) and all(c in "0123456789abcdefABCDEF" for c in value[1:]):
        return value if len(value) == 7 else "#" + "".join(c * 2 for c in value[1:])
    return "#111827"


def _draw_wrapped(draw, value, x, y, w, h, font, color, scale):
    return None
def _load_font(props):
    return None
