# GitHub Copilot — Workspace Instructions

This repository hosts a **Model Context Protocol (MCP) server** that generates market research questionnaires as Word `.docx` files. GitHub Copilot consumes the server via [`.vscode/mcp.json`](../.vscode/mcp.json); the cloud coding agent reads [`AGENTS.md`](../AGENTS.md).

## What this server is (and isn't)

- **Structural, not generative.** The server parses an Excel module workbook and a DOCX Jinja template, then renders questionnaires from JSON Copilot supplies. The server never composes question text; the Copilot LLM does.
- Two workflows depending on workbook shape:
  - **Module workflow (preferred).** Workbook has `core` + `industry__<industry>` + `unique__<industry>__<channel>` sheets. Pre-authored questions are pulled from each module, deduplicated, aligned, reviewed, translated, and rendered.
  - **Guidance workflow (legacy).** Workbook has one sheet per channel containing guidance text only. The LLM composes question text from the guidance.

## Multi-agent ecosystem

Defined in [`.github/agents/`](agents/):

| Agent | Role |
|---|---|
| **Questionnaire Orchestrator** | Entry point — gathers inputs, routes work, renders both EN and target-language .docx. |
| **Questionnaire Composer** | Pulls 3 modules, dedupes via `find_duplicate_candidates`, aligns sections, tailors to business. |
| **Questionnaire Reviewer** | QA checklist — flags blockers/fixes. Doesn't rewrite. |
| **Questionnaire Translator** | Idiomatic translation preserving structure. Not literal MTL. |

Skills they call (in [`.github/skills/`](skills/)):

- `dedupe-questions` — heuristic for resolving candidate duplicates across modules.
- `align-sections` — canonical section flow for survey design.
- `qa-review` — review checklist applied by the reviewer.
- `idiomatic-translate` — 4-pass translation method.

## MCP tools

**Module-flow tools (preferred):** `list_industries`, `list_channels_for_industry`, `get_core_module`, `get_industry_module`, `get_unique_module`, `assemble_modules`, `find_duplicate_candidates`, `translate_questionnaire`, `render_dual_language`.

**Legacy / shared tools:** `list_channels`, `get_channel_guide`, `get_template_structure`, `list_template_placeholders`, `list_supported_languages`, `get_country_locale`, `translate_text_blocks`, `render_questionnaire_docx`.

## Workflow Copilot follows when generating

The orchestrator drives this; users invoke via `/generate-questionnaire`:

1. `list_industries` → confirm with user.
2. `list_channels_for_industry(industry)` → confirm channel.
3. Hand off to **Composer**: `assemble_modules` → `find_duplicate_candidates` → align/dedupe → English `RenderRequest`.
4. Hand off to **Reviewer**: QA pass; loop if rejected.
5. If non-English target requested, hand off to **Translator**: produce target-language `RenderRequest`.
6. Orchestrator calls `render_dual_language(english_payload, translated_payload)`.
7. Deliver both `.docx` files.

Always confirm **language** and **country** with the user before rendering.

## Repo conventions

- **Python 3.11+**, FastMCP 2.x/3.x, Pydantic v2, Streamable HTTP transport at `/mcp`.
- Code lives under [`src/mcp_market_research/`](../src/mcp_market_research/). Tests under [`tests/`](../tests/).
- Real Excel files belong in [`assets/`](../assets/) (gitignored). Sample assets in [`src/mcp_market_research/samples/`](../src/mcp_market_research/samples/) — never edit those by hand; regenerate via [`scripts/generate_samples.py`](../scripts/generate_samples.py).
- Auth: API key via `Authorization: Bearer <key>` or `X-API-Key`. Keys come from `MCP_API_KEYS` (comma-separated for rotation). Never hardcode keys.
- Logging: `structlog` JSON. Each tool is wrapped with `@traced_tool(name)` recording `tool`, `duration_ms`, `request_id`.
- Errors: typed exceptions in [`errors.py`](../src/mcp_market_research/errors.py). Excel validation errors include sheet + row.

## Coding rules

- **Don't** add a feature flag, fallback, or compatibility shim unless asked.
- **Don't** mock the parsers or renderer in tests when a real fixture works — integration tests must produce a real `.docx`.
- **Don't** widen tool surface area without updating the agent files. New behavior usually goes into a skill or the LLM prompt, not new tools.
- Keep tool docstrings tight — they ship to Copilot as the tool description.
- Pydantic models are the contract. Update [`models/`](../src/mcp_market_research/models/) before changing tool signatures.
- All paths via `pathlib.Path` (Windows deployment target).

## Deployment target

- The user authors on macOS/VS Code but **deploys to Windows + Docker**. Don't add macOS-only tooling. PowerShell is the assumed shell in deployment docs.
- Production transport: Streamable HTTP behind Caddy auto-TLS. See [`docker-compose.yml`](../docker-compose.yml), [`Caddyfile`](../Caddyfile), [`Dockerfile`](../Dockerfile).
