from __future__ import annotations

import re
import statistics
import threading
from pathlib import Path

import pdfplumber

from ..errors import ConfigurationError, TemplateExtractionError
from ..models import Placeholder, TemplateStructure

PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Z][A-Z0-9_]+)\s*\}\}")
RESERVED_PLACEHOLDERS: dict[str, str] = {
    "COMPANY_NAME": "The brand or business commissioning the questionnaire.",
    "QUESTIONNAIRE_TITLE": "Title displayed at the top of the questionnaire.",
    "LANGUAGE": "ISO 639-1 language code, e.g. 'fr'.",
    "COUNTRY": "ISO 3166-1 alpha-2 country code, e.g. 'FR'.",
    "GENERATED_DATE": "Locale-formatted generation date.",
}

_cache_lock = threading.Lock()
_cache: dict[Path, tuple[float, TemplateStructure]] = {}


def extract_template_structure(path: Path) -> TemplateStructure:
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise ConfigurationError(f"PDF template not found at {resolved}")

    mtime = resolved.stat().st_mtime
    with _cache_lock:
        cached = _cache.get(resolved)
        if cached is not None and cached[0] == mtime:
            return cached[1]

    try:
        result = _extract(resolved)
    except Exception as exc:
        raise TemplateExtractionError(f"Failed to parse PDF '{resolved}': {exc}") from exc

    with _cache_lock:
        _cache[resolved] = (mtime, result)
    return result


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


def _extract(path: Path) -> TemplateStructure:
    sections: list[str] = []
    placeholders: dict[str, Placeholder] = {}
    page_count = 0

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        font_sizes: list[float] = []
        for page in pdf.pages:
            for char in page.chars:
                size = char.get("size")
                if isinstance(size, (int, float)):
                    font_sizes.append(float(size))

        median_size = statistics.median(font_sizes) if font_sizes else 0.0
        heading_threshold = median_size * 1.2

        for page in pdf.pages:
            full_text = page.extract_text() or ""
            for match in PLACEHOLDER_RE.finditer(full_text):
                key = match.group(1)
                if key not in placeholders:
                    placeholders[key] = Placeholder(
                        key=key,
                        reserved=key in RESERVED_PLACEHOLDERS,
                        hint=RESERVED_PLACEHOLDERS.get(key),
                    )

            for line in _iter_lines(page):
                line_text, max_size, is_bold = line
                if not line_text or PLACEHOLDER_RE.search(line_text):
                    continue
                if (
                    (max_size and max_size >= heading_threshold)
                    or (is_bold and len(line_text.split()) <= 8)
                ):
                    if line_text not in sections and len(line_text) <= 80:
                        sections.append(line_text)

    return TemplateStructure(
        sections=sections,
        placeholders=list(placeholders.values()),
        page_count=page_count,
        source_path=str(path),
    )


def _iter_lines(page: object) -> list[tuple[str, float, bool]]:
    """Group characters by visual line and return (text, max_font_size, is_bold) per line."""
    chars = getattr(page, "chars", [])
    if not chars:
        return []

    chars_sorted = sorted(chars, key=lambda c: (round(float(c.get("top", 0)), 1), float(c.get("x0", 0))))
    lines: list[tuple[str, float, bool]] = []
    current: list[dict[str, object]] = []
    current_top: float | None = None

    def flush() -> None:
        if not current:
            return
        text = "".join(str(c.get("text", "")) for c in current).strip()
        sizes = [float(c.get("size", 0) or 0) for c in current]
        bold_chars = sum(1 for c in current if "Bold" in str(c.get("fontname", "")))
        is_bold = bold_chars >= max(1, len(current) // 2)
        max_size = max(sizes) if sizes else 0.0
        if text:
            lines.append((text, max_size, is_bold))
        current.clear()

    for char in chars_sorted:
        top = round(float(char.get("top", 0)), 1)
        if current_top is None or abs(top - current_top) > 2.0:
            flush()
            current_top = top
        current.append(char)
    flush()

    return lines
