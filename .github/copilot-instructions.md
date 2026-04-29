# GitHub Copilot — Workspace Instructions

This repository hosts a **Model Context Protocol (MCP) server** that generates market research questionnaires as Word `.docx` files. GitHub Copilot in VS Code consumes the server via [`.vscode/mcp.json`](../.vscode/mcp.json); the cloud coding agent reads [`AGENTS.md`](../AGENTS.md).

## What this server is (and isn't)

- **Structural, not generative.** The server parses an Excel channel guide, a PDF reference template, and a DOCX Jinja template, then renders questionnaires from JSON Copilot supplies.
- **The Copilot LLM composes question text.** Tools never invent questions — they expose guidance and structure, and accept fully-composed payloads.
- Eight tools: `list_channels`, `get_channel_guide`, `get_template_structure`, `list_template_placeholders`, `list_supported_languages`, `get_country_locale`, `translate_text_blocks`, `render_questionnaire_docx`.

## Repo conventions

- **Python 3.11+**, FastMCP 2.x/3.x, Pydantic v2, Streamable HTTP transport at `/mcp`.
- Code lives under [`src/mcp_market_research/`](../src/mcp_market_research/). Tests under [`tests/`](../tests/).
- Real Excel/PDF/DOCX files belong in [`assets/`](../assets/) (gitignored). Sample assets in [`src/mcp_market_research/samples/`](../src/mcp_market_research/samples/) — never edit those by hand; regenerate via [`scripts/generate_samples.py`](../scripts/generate_samples.py).
- Auth: API key via `Authorization: Bearer <key>` or `X-API-Key`. Keys come from `MCP_API_KEYS` (comma-separated for rotation). Never hardcode keys.
- Logging: `structlog` JSON. Each tool is wrapped with `@traced_tool(name)` recording `tool`, `duration_ms`, `request_id`.
- Errors: typed exceptions in [`errors.py`](../src/mcp_market_research/errors.py). Excel validation errors include sheet + row.

## Workflow Copilot should follow when generating a questionnaire

1. Call `list_channels` to discover what's available.
2. Call `get_channel_guide(channel)` for sections, question types, guidance, examples.
3. Optionally call `get_template_structure` / `list_template_placeholders` if layout details matter.
4. **Compose** 5–15 well-targeted questions per section, tailored to the user's business — do **not** copy example fields verbatim.
5. If the user requested a non-English language, translate idiomatically. Use `translate_text_blocks` only as a fallback.
6. Call `render_questionnaire_docx` with the assembled `RenderRequest` JSON.
7. Return the `.docx` path / base64 to the user.

Always confirm **language** and **country** with the user before rendering.

## Coding rules

- **Don't** add a feature flag, fallback, or compatibility shim unless asked.
- **Don't** mock the parsers or renderer in tests when a real fixture works — integration tests must produce a real `.docx`.
- **Don't** widen tool surface area. New behavior goes into the LLM prompt or the renderer, not new tools.
- Keep tool docstrings tight — they ship to Copilot as the tool description.
- Pydantic models are the contract. Update [`models/`](../src/mcp_market_research/models/) before changing tool signatures.
- All paths via `pathlib.Path` (Windows deployment target).

## Deployment target

- The user authors on macOS/VS Code but **deploys to Windows + Docker**. Don't add macOS-only tooling. PowerShell is the assumed shell in deployment docs.
- Production transport: Streamable HTTP behind Caddy auto-TLS. See [`docker-compose.yml`](../docker-compose.yml), [`Caddyfile`](../Caddyfile), [`Dockerfile`](../Dockerfile).
