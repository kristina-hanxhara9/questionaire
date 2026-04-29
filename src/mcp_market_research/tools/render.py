from __future__ import annotations

from ..config import Settings
from ..logging_setup import log_extra, traced_tool
from ..models import DualLanguageRenderResult, RenderRequest, RenderResult
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


def render_dual_language_tool(
    settings: Settings,
    english_payload: RenderRequest,
    translated_payload: RenderRequest | None = None,
) -> DualLanguageRenderResult:
    """Render both the English questionnaire and (optionally) the translated copy.

    The agent supplies both fully-composed payloads. We don't translate here — that
    happens via the translator agent or `translate_questionnaire`."""

    @traced_tool("render_dual_language")
    def _impl() -> DualLanguageRenderResult:
        if english_payload.language != "en":
            log_extra(warning="english_payload.language != 'en'")

        english_result = render(
            template_path=settings.docx_template_path,
            payload=english_payload,
            output_dir=settings.output_dir,
        )
        translated_result: RenderResult | None = None
        if translated_payload is not None and translated_payload.language != "en":
            translated_result = render(
                template_path=settings.docx_template_path,
                payload=translated_payload,
                output_dir=settings.output_dir,
            )
        return DualLanguageRenderResult(english=english_result, translated=translated_result)

    return _impl()
