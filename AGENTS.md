# AGENTS.md — GitHub Copilot Coding Agent

Instructions for the GitHub Copilot **cloud coding agent** (and other agentic AI tooling) working in this repository. For the VS Code chat agent, see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Project summary

A Python MCP (Model Context Protocol) server that generates market research questionnaires as Word `.docx` files. The server is **structural** — it parses an Excel module workbook (or a legacy guidance workbook), a PDF reference layout, and a DOCX Jinja template, then renders questionnaires from JSON the calling LLM supplies. The server never composes question text.

The repo ships a **4-agent GitHub Copilot pipeline** (orchestrator → composer → reviewer → translator) defined in [`.github/agents/`](.github/agents/) plus 4 reusable skills in [`.github/skills/`](.github/skills/). The multi-agent flow assembles three modules (core ~84 + industry standard ~74 + channel-unique ~6), dedupes near-overlaps, aligns sections, runs a QA pass, translates idiomatically, and renders **both** an English and a target-language `.docx` in a single call.

## Setup

```powershell
# Windows / PowerShell (production target)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python scripts/generate_samples.py
copy .env.example .env
# Edit .env to set MCP_API_KEYS=dev-key
```

```bash
# macOS / Linux (authoring only)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/generate_samples.py
cp .env.example .env
```

## Run locally

```powershell
python -m mcp_market_research
# Listening on http://localhost:8080/mcp
```

Smoke test:

```powershell
curl -X POST http://localhost:8080/mcp `
  -H "Authorization: Bearer dev-key" `
  -H "Content-Type: application/json" `
  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'
```

## Tests

```bash
pytest -q                  # unit + integration + contract
pytest tests/unit -q       # fast loop
pytest tests/integration   # writes a real .docx to output/
```

Integration tests must produce a real `.docx` — **don't mock the renderer**. If a test fails because a sample asset is missing, run `python scripts/generate_samples.py`.

## Lint / type-check

```bash
ruff check src tests
ruff format src tests
mypy src
```

## Code map

- [`src/mcp_market_research/server.py`](src/mcp_market_research/server.py) — FastMCP app, tool registration, `/healthz`, `/readyz`.
- [`src/mcp_market_research/config.py`](src/mcp_market_research/config.py) — pydantic-settings; falls back to bundled samples when env paths are missing.
- [`src/mcp_market_research/auth.py`](src/mcp_market_research/auth.py) — Bearer / `X-API-Key` middleware with constant-time compare.
- [`src/mcp_market_research/parsers/module_workbook.py`](src/mcp_market_research/parsers/module_workbook.py) — module workbook parser (`core` + `industry__*` + `unique__*` sheets), mtime cache.
- [`src/mcp_market_research/parsers/excel_guide.py`](src/mcp_market_research/parsers/excel_guide.py) — legacy multi-sheet openpyxl parser, mtime cache. Skips module-shaped sheets.
- [`src/mcp_market_research/parsers/pdf_template.py`](src/mcp_market_research/parsers/pdf_template.py) — pdfplumber structure extractor.
- [`src/mcp_market_research/renderers/docx_renderer.py`](src/mcp_market_research/renderers/docx_renderer.py) — docxtpl + python-docx, locale-aware date, RTL via `w:bidi`.
- [`src/mcp_market_research/tools/`](src/mcp_market_research/tools/) — one module per tool group (`modules.py` for the multi-agent flow, `channels.py` for legacy). Each tool is wrapped with `@traced_tool(name)`.
- [`src/mcp_market_research/models/`](src/mcp_market_research/models/) — Pydantic v2 schemas (`module.py` for the new flow). Update these *before* changing tool signatures.
- [`.github/agents/`](.github/agents/) — 4 specialist agents (orchestrator/composer/reviewer/translator). Update when tool surface changes.
- [`.github/skills/`](.github/skills/) — 4 skills (dedupe-questions, align-sections, qa-review, idiomatic-translate). Behavior changes go here, not into new tools.
- [`scripts/generate_samples.py`](scripts/generate_samples.py) — regenerates `samples/` Excel/PDF/DOCX (including `sample_modules.xlsx`). Don't hand-edit those binaries.

## Conventions

- **Python 3.11+.** `pathlib.Path` everywhere — no `os.path.join`.
- **Pydantic v2** for tool I/O. Tool docstrings ship to Copilot as the tool description; keep them tight.
- **Errors** are typed exceptions from [`errors.py`](src/mcp_market_research/errors.py). Excel validation errors must include sheet name + 1-based row. Module workbook errors raise `IndustryNotFoundError` / `ModuleNotFoundError`.
- **Logging:** `structlog` JSON. Don't `print()`.
- **API keys** come from the `MCP_API_KEYS` env var (comma-separated). Never hardcode.
- **Stable question IDs** (e.g. `core_001`, `opt_std_023`, `opt_sm_004`) are required and must be unique across the entire module workbook — they're how the composer/reviewer/translator track questions through the pipeline.
- **New behavior usually goes into a skill** ([`.github/skills/`](.github/skills/)) or the agent prompt — *not* a new MCP tool. Tools should stay deterministic and structural.
- **No new tools** without updating the relevant agent in [`.github/agents/`](.github/agents/) and [`README.md`](README.md).

## What this server is NOT

- Not a generator. The MCP client's LLM composes questions; we render them.
- Not multi-tenant. One Excel guide, one PDF, one DOCX template per deployment.
- Not stateful. Filesystem output only; no database.

## Pull request rules

- One change per PR. Don't bundle refactors with feature work.
- Tests must pass — including integration tests that produce a `.docx`.
- Update [`README.md`](README.md) tool catalog if you add or rename a tool.
- If you change the `RenderRequest` shape, update [`.github/agents/`](.github/agents/) (especially the composer + translator) so Copilot stays in sync.
- If you change the module workbook schema (sheet naming, required columns, ID format), update [`.github/instructions/templates.instructions.md`](.github/instructions/templates.instructions.md) and [`scripts/generate_samples.py`](scripts/generate_samples.py) in the same PR.
