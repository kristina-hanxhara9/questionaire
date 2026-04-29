from __future__ import annotations

from ..config import Settings
from ..logging_setup import log_extra, traced_tool
from ..models import RenderRequest, RenderResult
from ..renderers.docx_renderer import render


def render_questionnaire_docx_tool(
    settings: Settings, payload: RenderRequest
) -> RenderResult:
    @traced_tool("render_questionnaire_docx")
    def _impl() -> RenderResult:
        log_extra(language=payload.language, company=payload.company_name)
        return render(
            template_path=settings.docx_template_path,
            payload=payload,
            output_dir=settings.output_dir,
        )

    return _impl()
