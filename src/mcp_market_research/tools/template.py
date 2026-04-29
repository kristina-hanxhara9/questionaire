from __future__ import annotations

from ..config import Settings
from ..logging_setup import traced_tool
from ..models import Placeholder, TemplateStructure
from ..parsers.pdf_template import extract_template_structure


def get_template_structure_tool(settings: Settings) -> TemplateStructure:
    @traced_tool("get_template_structure")
    def _impl() -> TemplateStructure:
        return extract_template_structure(settings.pdf_template_path)

    return _impl()


def list_template_placeholders_tool(settings: Settings) -> list[Placeholder]:
    @traced_tool("list_template_placeholders")
    def _impl() -> list[Placeholder]:
        return extract_template_structure(settings.pdf_template_path).placeholders

    return _impl()
