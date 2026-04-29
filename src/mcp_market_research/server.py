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
    IndustryNotFoundError,
    LocaleNotSupportedError,
    ModuleNotFoundError,
    QuestionnaireError,
    RenderingError,
    TemplateExtractionError,
    TranslationError,
)
from .logging_setup import get_logger
from .models import (
    ChannelGuide,
    DualLanguageRenderResult,
    DuplicateCandidate,
    LocaleInfo,
    Module,
    ModuleQuestion,
    ModuleSet,
    Placeholder,
    RenderRequest,
    RenderResult,
    TemplateStructure,
)
from .tools import (
    assemble_modules_tool,
    find_duplicate_candidates_tool,
    get_channel_guide_tool,
    get_core_module_tool,
    get_country_locale_tool,
    get_industry_module_tool,
    get_template_structure_tool,
    get_unique_module_tool,
    list_channels_for_industry_tool,
    list_channels_tool,
    list_industries_tool,
    list_supported_languages_tool,
    list_template_placeholders_tool,
    render_dual_language_tool,
    render_questionnaire_docx_tool,
    translate_questionnaire_tool,
    translate_text_blocks_tool,
)


SERVER_INSTRUCTIONS = """\
Generate market research questionnaires for businesses, in any language and country.

This server supports two workflows depending on how the workbook is structured.

================================================================================
A) MODULE WORKFLOW (preferred — pre-authored questions in 3 modules)
================================================================================

The Excel workbook contains:
  - one `core` sheet (channel-agnostic, industry-agnostic core questions, ~84)
  - one `industry__<industry>` sheet per industry (industry standard, ~74 each)
  - one `unique__<industry>__<channel>` sheet per industry × channel (~6 each)

Workflow:
1. Call `list_industries` and `list_channels_for_industry(industry)` to discover.
2. Call `assemble_modules(industry, channel)` to fetch all three modules at once.
3. Concatenate the questions, then call `find_duplicate_candidates(questions)` to
   surface near-duplicates across modules. Use your judgment to merge or drop.
4. Reorder/regroup sections so the questionnaire flows naturally for the audience.
5. Run a QA pass: no double-barreled questions, options are mutually exclusive,
   required flags are sensible, demographic/consent questions are at the end.
6. Build a RenderRequest in English first.
7. If a non-English target language is requested, build a SECOND RenderRequest with
   the same structure but translated text. Translate idiomatically yourself, or fall
   back to `translate_questionnaire` for a deterministic pass.
8. Call `render_dual_language` to render BOTH the English and target-language .docx.

================================================================================
B) GUIDANCE WORKFLOW (fallback — workbook only has channel guidance)
================================================================================

If `list_industries` returns empty, use the legacy guidance flow:
1. `list_channels` → `get_channel_guide(channel)` → compose questions yourself
   from the guidance.
2. `translate_text_blocks` (optional).
3. `render_questionnaire_docx` with the composed payload.

================================================================================

Always confirm language + country with the user before rendering. The server is
structural — it provides modules, structure, and rendering. The LLM (you) handles
composition, dedup decisions, alignment, idiomatic translation, and QA.\
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

    @app.tool(
        name="list_industries",
        description=(
            "List industries configured in the module workbook (one '_industry__<industry>' "
            "sheet per entry). Empty if the workbook is in legacy guidance-only mode."
        ),
    )
    def list_industries() -> list[str]:
        return list_industries_tool(settings)

    @app.tool(
        name="list_channels_for_industry",
        description=(
            "List channels with a unique-question sheet for the given industry "
            "(via 'unique__<industry>__<channel>' sheets)."
        ),
    )
    def list_channels_for_industry(industry: str) -> list[str]:
        return list_channels_for_industry_tool(settings, industry)

    @app.tool(
        name="get_core_module",
        description=(
            "Return the channel-agnostic, industry-agnostic CORE module — questions asked "
            "in every questionnaire. Sourced from the workbook's 'core' sheet."
        ),
    )
    def get_core_module() -> Module:
        return get_core_module_tool(settings)

    @app.tool(
        name="get_industry_module",
        description=(
            "Return the INDUSTRY STANDARD module for one industry — channel-agnostic, "
            "industry-specific questions asked in every channel for that industry."
        ),
    )
    def get_industry_module(industry: str) -> Module:
        return get_industry_module_tool(settings, industry)

    @app.tool(
        name="get_unique_module",
        description=(
            "Return the UNIQUE module for one industry × channel combination — the small set "
            "of questions specific to that channel for that industry (typically ~6)."
        ),
    )
    def get_unique_module(industry: str, channel: str) -> Module:
        return get_unique_module_tool(settings, industry, channel)

    @app.tool(
        name="assemble_modules",
        description=(
            "Convenience: fetch all three modules (core + industry standard + unique) for "
            "one industry × channel in a single call. The agent then aligns and dedupes."
        ),
    )
    def assemble_modules(industry: str, channel: str) -> ModuleSet:
        return assemble_modules_tool(settings, industry, channel)

    @app.tool(
        name="find_duplicate_candidates",
        description=(
            "Surface candidate near-duplicate question pairs by tag overlap + normalized text "
            "similarity. The agent decides which to merge — this tool never drops questions."
        ),
    )
    def find_duplicate_candidates(
        questions: list[ModuleQuestion],
        similarity_threshold: float = 0.78,
    ) -> list[DuplicateCandidate]:
        return find_duplicate_candidates_tool(
            questions=questions, similarity_threshold=similarity_threshold
        )

    @app.tool(
        name="translate_questionnaire",
        description=(
            "Deterministic translation of a fully-composed RenderRequest into another language, "
            "preserving structure (section count, question order, options, required flags). "
            "Prefer translating idiomatically yourself; this is a fallback."
        ),
    )
    def translate_questionnaire(
        payload: RenderRequest,
        target_language: str,
        source_language: str = "en",
    ) -> RenderRequest:
        return translate_questionnaire_tool(
            settings,
            payload=payload,
            target_language=target_language,
            source_language=source_language,
        )

    @app.tool(
        name="render_dual_language",
        description=(
            "Render BOTH the English questionnaire and (optionally) the translated copy in one "
            "call. The translated payload is rendered only if its language != 'en'."
        ),
    )
    def render_dual_language(
        english_payload: RenderRequest,
        translated_payload: RenderRequest | None = None,
    ) -> DualLanguageRenderResult:
        return render_dual_language_tool(
            settings,
            english_payload=english_payload,
            translated_payload=translated_payload,
        )


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
    if isinstance(exc, IndustryNotFoundError):
        return {"code": -32602, "message": str(exc), "data": {"available": exc.available}}
    if isinstance(exc, ModuleNotFoundError):
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
