"""Official versioned template JSON schema and validation.

This schema is the single source of truth shared by:
- the PDF-to-JSON importer,
- the admin visual template builder,
- the Flutter renderer,
- the server-side PDF renderer.

Geometry is expressed in points on a page coordinate system with origin at
the top-left corner of the page.
"""

SCHEMA_VERSION = "1.0"

PAGE_SIZES = {
    "a4": {"width": 595.28, "height": 841.89},
    "letter": {"width": 612.0, "height": 792.0},
}

ELEMENT_TYPES = {"text", "image", "rect", "line", "ellipse", "icon"}

TEXT_ALIGN = {"left", "center", "right", "justify"}


def page_dimensions(page_size):
    return PAGE_SIZES.get(page_size, PAGE_SIZES["a4"])


def element_common_defaults():
    return {
        "id": None,
        "type": "text",
        "x": 0.0,
        "y": 0.0,
        "width": 100.0,
        "height": 20.0,
        "rotation": 0.0,
        "z": 0,
        "locked": False,
        "field": None,
        "dataSource": "static",  # static | cv | photo
        "defaultImage": None,  # shared asset key, e.g. avatar_01
        "allowUserUpload": False,
    }


def _validate_element(element, errors, index):
    common = element_common_defaults()
    etype = element.get("type")
    if etype not in ELEMENT_TYPES:
        errors.append(f"elements[{index}].type '{etype}' is not supported")
    for key in ("x", "y", "width", "height"):
        value = element.get(key, common[key])
        if not isinstance(value, (int, float)) or value < 0:
            errors.append(f"elements[{index}].{key} must be a non-negative number")
    if etype == "text":
        props = element.get("textProps", {})
        if props.get("align") not in (None, "left", "center", "right", "justify"):
            errors.append(f"elements[{index}].textProps.align invalid")
    if etype == "image":
        source = element.get("dataSource", element.get("field") and "photo" or "static")
        if element.get("allowUserUpload") and not element.get("field"):
            errors.append(f"elements[{index}] allowUserUpload requires a 'field'")


def validate_template_json(definition):
    """Return (ok, normalized_definition, errors)."""
    errors = []
    if not isinstance(definition, dict):
        return False, {}, ["definition must be a JSON object"]
    normalized = dict(definition)
    normalized["schema_version"] = definition.get("schema_version", SCHEMA_VERSION)
    if normalized["schema_version"] != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version '{normalized['schema_version']}'")
    pages = definition.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append("definition.pages must be a non-empty list")
        pages = []
    settings = definition.get("settings", {})
    normalized["settings"] = {
        "page_size": settings.get("page_size", "a4"),
        "margin": settings.get("margin", 36),
    }
    clean_pages = []
    for p_index, page in enumerate(pages):
        page_out = {
            "id": page.get("id") or f"page_{p_index + 1}",
            "background": page.get("background", "#FFFFFF"),
            "elements": [],
        }
        for e_index, element in enumerate(page.get("elements", [])):
            merged = {**element_common_defaults(), **element}
            _validate_element(merged, errors, e_index)
            page_out["elements"].append(merged)
        clean_pages.append(page_out)
    normalized["pages"] = clean_pages
    return len(errors) == 0, normalized, errors
