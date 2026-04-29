"""Contract tests: verify the MCP server registers the expected tools."""

from __future__ import annotations

from typing import Any

import pytest

from mcp_market_research.server import build_app

EXPECTED_TOOLS = {
    "list_channels",
    "get_channel_guide",
    "get_template_structure",
    "list_template_placeholders",
    "list_supported_languages",
    "get_country_locale",
    "translate_text_blocks",
    "render_questionnaire_docx",
}


@pytest.mark.contract
def test_server_registers_all_expected_tools(settings: Any) -> None:
    app = build_app(settings)
    tools_attr = getattr(app, "_tools", None) or getattr(app, "tools", None)
    if tools_attr is None and hasattr(app, "_tool_manager"):
        tools_attr = app._tool_manager._tools  # type: ignore[attr-defined]
    assert tools_attr is not None, "Could not access registered tools on FastMCP instance"

    if isinstance(tools_attr, dict):
        names = set(tools_attr.keys())
    else:
        names = {getattr(t, "name", str(t)) for t in tools_attr}

    assert EXPECTED_TOOLS <= names, f"missing tools: {EXPECTED_TOOLS - names}"


@pytest.mark.contract
def test_server_has_health_route(settings: Any) -> None:
    app = build_app(settings)
    starlette = None
    for attr in ("_starlette_app", "starlette_app"):
        starlette = getattr(app, attr, None)
        if starlette is not None:
            break
    if starlette is None and hasattr(app, "streamable_http_app"):
        starlette = app.streamable_http_app()
    assert starlette is not None

    paths = []
    for route in getattr(starlette, "routes", []):
        path = getattr(route, "path", None)
        if path:
            paths.append(path)
    assert "/healthz" in paths
