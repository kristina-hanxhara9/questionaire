from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import __version__
from .auth import APIKeyMiddleware
from .config import Settings, get_settings
from .errors import (
    ChannelNotFoundError,
    ConfigurationError,
    ExcelGuideValidationError,
    LocaleNotSupportedError,
    QuestionnaireError,
    RenderingError,
    TemplateExtractionError,
    TranslationError,
)
from .logging_setup import get_logger
from .models import (
    ChannelGuide,
    LocaleInfo,
    Placeholder,
    RenderRequest,
    RenderResult,
    TemplateStructure,
)
from .tools import (
    get_channel_guide_tool,
    get_country_locale_tool,
    get_template_structure_tool,
    list_channels_tool,
    list_supported_languages_tool,
    list_template_placeholders_tool,
    render_questionnaire_docx_tool,
    translate_text_blocks_tool,
)


SERVER_INSTRUCTIONS = """\
Generate market research questionnaires for businesses, in any language and country.

WORKFLOW for the calling agent:
1. Call `list_channels` to see what channels (e.g., social_media, email, in_store) are available.
2. Call `get_channel_guide(channel)` to retrieve sections + question types + guidance + examples.
3. Compose questions yourself using the guidance, tailored to the user's business context.
4. Call `get_template_structure` to see the document layout (sections, placeholders).
5. Optionally call `translate_text_blocks` if you want a deterministic translation pass; otherwise translate idiomatically yourself.
6. Optionally call `get_country_locale` to format dates correctly for the target country.
7. Call `render_questionnaire_docx` with the assembled JSON to produce the final .docx.

The server is structural — it does NOT compose question text. You do that with your LLM.\
"""


def build_app(settings: Settings | None = None) -> FastMCP:
    settings = settings or get_settings()
    log = get_logger("mcp.server")

    if settings.using_sample_excel:
        log.warning(
            "using_sample_asset",
            asset="excel",
            path=str(settings.excel_guide_path),
            note="Set EXCEL_GUIDE_PATH to your real channel workbook.",
        )
    if settings.using_sample_pdf:
        log.warning("using_sample_asset", asset="pdf", path=str(settings.pdf_template_path))
    if settings.using_sample_docx:
        log.warning("using_sample_asset", asset="docx", path=str(settings.docx_template_path))

    settings.output_dir.mkdir(parents=True, exist_ok=True)

    app = FastMCP(
        name="market-research-questionnaire",
        instructions=SERVER_INSTRUCTIONS,
    )

    _register_tools(app, settings)
    _register_health_routes(app)
    _wrap_with_auth(app, settings)

    log.info(
        "server_ready",
        version=__version__,
        host=settings.host,
        port=settings.port,
        excel=str(settings.excel_guide_path),
        pdf=str(settings.pdf_template_path),
        docx=str(settings.docx_template_path),
        output=str(settings.output_dir),
    )
    return app


def _register_tools(app: FastMCP, settings: Settings) -> None:
    @app.tool(
        name="list_channels",
        description=(
            "List all available channels (one per Excel sheet). Call this first to discover "
            "what kinds of questionnaires are supported."
        ),
    )
    def list_channels() -> list[str]:
        return list_channels_tool(settings)

    @app.tool(
        name="get_channel_guide",
        description=(
            "Return the structured guidance for a channel: sections, question types, examples, "
            "and required flags. Use this guidance to compose questions tailored to the business."
        ),
    )
    def get_channel_guide(channel: str) -> ChannelGuide:
        return get_channel_guide_tool(settings, channel)

    @app.tool(
        name="get_template_structure",
        description=(
            "Extract the layout structure of the PDF reference template — sections, placeholders, "
            "page count. The PDF is a layout reference; the .docx template renders the output."
        ),
    )
    def get_template_structure() -> TemplateStructure:
        return get_template_structure_tool(settings)

    @app.tool(
        name="list_template_placeholders",
        description="List all {{KEY}} placeholders the template expects.",
    )
    def list_template_placeholders() -> list[Placeholder]:
        return list_template_placeholders_tool(settings)

    @app.tool(
        name="list_supported_languages",
        description="ISO codes for languages the deterministic translator supports.",
    )
    def list_supported_languages() -> list[LocaleInfo]:
        return list_supported_languages_tool()

    @app.tool(
        name="get_country_locale",
        description=(
            "Return locale info (date format, decimal separator, RTL flag, native names) for an "
            "ISO 3166-1 alpha-2 country code, optionally combined with a language."
        ),
    )
    def get_country_locale(country_code: str, language: str | None = None) -> LocaleInfo:
        return get_country_locale_tool(country_code=country_code, language=language)

    @app.tool(
        name="translate_text_blocks",
        description=(
            "Translate a list of strings to the target language using the bundled deep-translator "
            "backend. Use only if you want deterministic translation; otherwise translate "
            "idiomatically yourself."
        ),
    )
    def translate_text_blocks(
        blocks: list[str], target_language: str, source_language: str = "en"
    ) -> list[str]:
        return translate_text_blocks_tool(
            settings, blocks=blocks, target_language=target_language, source_language=source_language
        )

    @app.tool(
        name="render_questionnaire_docx",
        description=(
            "Render the final questionnaire as a .docx using the template. Pass the full "
            "RenderRequest payload with composed sections and questions."
        ),
    )
    def render_questionnaire_docx(payload: RenderRequest) -> RenderResult:
        return render_questionnaire_docx_tool(settings, payload)


def _register_health_routes(app: FastMCP) -> None:
    @app.custom_route("/healthz", methods=["GET"])
    async def healthz(request: Request) -> JSONResponse:  # noqa: ARG001
        return JSONResponse({"status": "ok", "version": __version__})

    @app.custom_route("/readyz", methods=["GET"])
    async def readyz(request: Request) -> JSONResponse:  # noqa: ARG001
        return JSONResponse({"status": "ready", "version": __version__})


def _wrap_with_auth(app: FastMCP, settings: Settings) -> None:
    """Attach the API-key middleware to the underlying ASGI app."""
    starlette_app: Any | None = getattr(app, "_starlette_app", None) or getattr(
        app, "starlette_app", None
    )
    if starlette_app is None:
        try:
            starlette_app = app.streamable_http_app()  # type: ignore[attr-defined]
        except AttributeError:
            starlette_app = None
    if starlette_app is not None and hasattr(starlette_app, "add_middleware"):
        starlette_app.add_middleware(APIKeyMiddleware, settings=settings)


def map_exception(exc: Exception) -> dict[str, Any]:
    """Translate domain exceptions into MCP-friendly error payloads (used by tests)."""
    if isinstance(exc, ChannelNotFoundError):
        return {"code": -32602, "message": str(exc), "data": {"available": exc.available}}
    if isinstance(exc, ExcelGuideValidationError):
        return {"code": -32602, "message": "Invalid Excel guide", "data": {"errors": exc.errors}}
    if isinstance(exc, LocaleNotSupportedError):
        return {"code": -32602, "message": str(exc)}
    if isinstance(exc, ConfigurationError):
        return {"code": -32000, "message": str(exc)}
    if isinstance(exc, TemplateExtractionError):
        return {"code": -32000, "message": str(exc)}
    if isinstance(exc, RenderingError):
        return {"code": -32000, "message": str(exc)}
    if isinstance(exc, TranslationError):
        return {"code": -32000, "message": str(exc)}
    if isinstance(exc, QuestionnaireError):
        return {"code": -32000, "message": str(exc)}
    return {"code": -32603, "message": "Internal error", "data": {"detail": str(exc)}}
