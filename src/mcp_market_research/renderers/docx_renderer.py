from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docxtpl import DocxTemplate

from ..errors import ConfigurationError, RenderingError
from ..models import LocaleInfo, RenderRequest, RenderResult
from ..tools.locale import get_country_locale_info, format_date

INLINE_BYTES_LIMIT = 4 * 1024 * 1024  # 4 MB


def render(template_path: Path, payload: RenderRequest, output_dir: Path) -> RenderResult:
    template = Path(template_path).resolve()
    if not template.exists():
        raise ConfigurationError(f"DOCX template not found at {template}")

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    locale = _resolve_locale(payload)
    context = _build_context(payload, locale)

    try:
        doc = DocxTemplate(str(template))
        doc.render(context)
    except Exception as exc:
        raise RenderingError(f"Template rendering failed: {exc}") from exc

    filename = _build_filename(payload)
    out_path = output_dir / filename

    try:
        doc.save(str(out_path))
    except Exception as exc:
        raise RenderingError(f"Failed to save rendered file: {exc}") from exc

    if locale.rtl:
        _apply_rtl(out_path)

    size = out_path.stat().st_size
    bytes_b64: str | None = None
    if size <= INLINE_BYTES_LIMIT:
        bytes_b64 = base64.b64encode(out_path.read_bytes()).decode("ascii")

    return RenderResult(
        path=str(out_path),
        filename=filename,
        bytes_b64=bytes_b64,
        size_bytes=size,
    )


def _resolve_locale(payload: RenderRequest) -> LocaleInfo:
    if payload.country_code:
        return get_country_locale_info(payload.country_code, payload.language)
    return get_country_locale_info(None, payload.language)


def _build_context(payload: RenderRequest, locale: LocaleInfo) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    context: dict[str, object] = {
        "company_name": payload.company_name,
        "questionnaire_title": payload.title,
        "language": payload.language,
        "country_code": payload.country_code or "",
        "country": payload.country_code or "",
        "generated_date": format_date(now, locale),
        "sections": [s.model_dump() for s in payload.sections],
    }
    for key, value in payload.extra_placeholders.items():
        context[key] = value
        context[key.lower()] = value
    return context


def _build_filename(payload: RenderRequest) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", payload.company_name.lower()).strip("-") or "company"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"questionnaire_{slug}_{payload.language}_{timestamp}.docx"


def _apply_rtl(path: Path) -> None:
    """Set bidi=true on every paragraph for RTL languages."""
    try:
        from docx.oxml.ns import qn  # noqa: PLC0415

        doc = Document(str(path))
        for paragraph in doc.paragraphs:
            p_pr = paragraph._p.get_or_add_pPr()
            bidi = p_pr.find(qn("w:bidi"))
            if bidi is None:
                from docx.oxml import OxmlElement  # noqa: PLC0415

                bidi_el = OxmlElement("w:bidi")
                bidi_el.set(qn("w:val"), "1")
                p_pr.append(bidi_el)
        doc.save(str(path))
    except Exception as exc:
        raise RenderingError(f"Failed to apply RTL formatting: {exc}") from exc
