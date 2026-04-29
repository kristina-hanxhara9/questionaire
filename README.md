# questionaire

An MCP server that lets **GitHub Copilot** agents generate market research questionnaires — in any language, for any country — through a 4-agent pipeline:

1. **Composer** — assembles questions from a 3-module workbook (core 84 + industry standard 74 + channel-unique 6), deduplicates near-overlaps, and aligns them into the canonical section flow.
2. **Reviewer** — runs a survey-design QA pass; flags blockers/fixes.
3. **Translator** — produces an idiomatic target-language version (not a literal translation), preserving structure for the renderer.
4. **Orchestrator** — gathers inputs, routes between specialists, renders **both English and target-language `.docx`** in one call.

The server is **structural, not generative**. The Copilot LLM does the composition, dedup decisions, alignment, idiomatic translation, and QA — this server provides deterministic tools (parse Excel, parse PDF, render DOCX, localize, find duplicate candidates, translate as fallback).

> Designed for users with GitHub Copilot Business / Enterprise but **no Azure subscription**. Copilot's LLM does the creative work; this MCP server does the structural work.

The repo ships first-class GitHub Copilot integration:

- [`.vscode/mcp.json`](.vscode/mcp.json) — VS Code Copilot picks up the server automatically.
- [`.github/agents/`](.github/agents/) — the 4 specialist agents (orchestrator, composer, reviewer, translator).
- [`.github/skills/`](.github/skills/) — 4 skills they call (dedupe-questions, align-sections, qa-review, idiomatic-translate).
- [`.github/prompts/generate-questionnaire.prompt.md`](.github/prompts/generate-questionnaire.prompt.md) — reusable `/generate-questionnaire` prompt.
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — workspace context for Copilot.
- [`AGENTS.md`](AGENTS.md) — instructions for the GitHub Copilot **cloud coding agent**.

---

## Architecture

```
                       GitHub Copilot (VS Code or Cloud Agent)
                                       │
                                       ▼
                     ┌────────── Orchestrator ──────────┐
                     │                                   │
            ┌────────┴────────┐                          │
            ▼                 ▼                          ▼
        Composer ─────▶ Reviewer ──▶ Translator ──▶ render_dual_language
            │                                              │
            └─ MCP tools (assemble_modules,                │
               find_duplicate_candidates, …)               ▼
                                                  EN .docx + <lang> .docx

        MCP server (Streamable HTTP, behind Caddy auto-TLS)
            ├─ openpyxl        → core / industry / unique modules
            ├─ pdfplumber      → template structure
            ├─ docxtpl         → DOCX render
            ├─ deep-translator → fallback translation
            └─ Babel           → country localization
```

---

## Quickstart (Windows / PowerShell)

```powershell
# 1. Clone and enter
git clone git@github.com:kristina-hanxhara9/questionaire.git
cd questionaire

# 2. Create a venv and install
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -e .

# 3. Generate the bundled sample assets (Excel, PDF, DOCX)
py scripts\generate_samples.py

# 4. Configure
copy .env.example .env
# Edit .env — at minimum set MCP_API_KEYS to a strong random value.
# Generate one with:  py -c "import secrets; print(secrets.token_urlsafe(32))"

# 5. Run
py -m mcp_market_research
# Listening on 0.0.0.0:8080
```

Hit the health endpoint:

```powershell
curl http://localhost:8080/healthz
# {"status":"ok","version":"0.1.0"}
```

List the tools:

```powershell
$key = (Get-Content .env | Select-String '^MCP_API_KEYS=').ToString().Split('=')[1]
$body = '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
curl -X POST http://localhost:8080/mcp `
  -H "Authorization: Bearer $key" `
  -H "Content-Type: application/json" `
  -d $body
```

---

## MCP tools

### Module workflow (preferred)

| Tool | Purpose |
|---|---|
| `list_industries()` | Industries configured in the workbook |
| `list_channels_for_industry(industry)` | Channels with a unique-question sheet for the industry |
| `get_core_module()` | Channel-agnostic, industry-agnostic core questions |
| `get_industry_module(industry)` | Industry-standard, channel-agnostic questions |
| `get_unique_module(industry, channel)` | Industry × channel unique questions |
| `assemble_modules(industry, channel)` | Convenience: all 3 modules in one call |
| `find_duplicate_candidates(questions, ...)` | Surface near-duplicate pairs by tag overlap + text similarity |
| `translate_questionnaire(payload, target_language)` | Deterministic translation preserving structure (fallback) |
| `render_dual_language(en_payload, translated_payload)` | Render BOTH English and target-language `.docx` |

### Shared / legacy

| Tool | Purpose |
|---|---|
| `list_channels()` | Channel sheets from a legacy guidance workbook |
| `get_channel_guide(channel)` | Guidance for legacy channel sheet |
| `get_template_structure()` | PDF section headings + placeholders |
| `list_template_placeholders()` | All `{{KEY}}` tokens with hints |
| `list_supported_languages()` | ISO codes + native names |
| `get_country_locale(country, language?)` | Date format, decimal separator, RTL flag |
| `translate_text_blocks(blocks, target, source="en")` | Deterministic string translation |
| `render_questionnaire_docx(payload)` | Render a single `.docx` |

---

## Connecting to GitHub Copilot

### Path A — VS Code Copilot Chat (recommended first)

The repo ships [`.vscode/mcp.json`](.vscode/mcp.json) — VS Code wires the server in automatically.

1. Open the repo in VS Code (with the **GitHub Copilot** + **GitHub Copilot Chat** extensions installed).
2. **Command Palette** → **MCP: List Servers** → pick **questionnaire** → **Start Server**. VS Code prompts for the URL (`http://localhost:8080/mcp` or your production URL) and the bearer token (one of `MCP_API_KEYS`).
3. **Copilot Chat** → switch to **Agent** mode → confirm the 8 tools are enabled in the tools picker.
4. Try: *"Generate a social media questionnaire for Acme Corp in English."* Copilot calls `list_channels` → `get_channel_guide` → `render_questionnaire_docx` and returns a `.docx`.

Bonus: the **Questionnaire Generator** custom agent ([`.github/agents/questionnaire-generator.agent.md`](.github/agents/questionnaire-generator.agent.md)) and the `/generate-questionnaire` prompt file ([`.github/prompts/generate-questionnaire.prompt.md`](.github/prompts/generate-questionnaire.prompt.md)) come pre-configured.

### Path B — GitHub Copilot Cloud Coding Agent

1. Deploy the server to a public HTTPS URL (see [Production deployment](#production-deployment)).
2. GitHub repo → **Settings** → **Copilot** → **Coding agent** → **Model Context Protocol** → **Add server**.
3. Name `questionnaire`, type `http`, URL `https://<your-host>/mcp`, header `Authorization: Bearer <your-key>` (use repo / org secrets).
4. The cloud agent reads [`AGENTS.md`](AGENTS.md) for repo conventions automatically.

### Path C — Other MCP clients

The same URL + bearer token works in Claude Code, Claude Desktop, Cursor, and any official MCP SDK. See [`deploy/github-copilot-setup.md`](deploy/github-copilot-setup.md) for the full walkthrough.

---

## Configuration

All settings are environment variables (see [`.env.example`](.env.example)):

| Variable | Default | Purpose |
|---|---|---|
| `MCP_API_KEYS` | *required* | Comma-separated bearer tokens (rotation-friendly) |
| `EXCEL_GUIDE_PATH` | bundled sample | Multi-sheet `.xlsx` (one sheet per channel) |
| `PDF_TEMPLATE_PATH` | bundled sample | Layout reference PDF |
| `DOCX_TEMPLATE_PATH` | bundled sample | docxtpl Jinja2 `.docx` template |
| `OUTPUT_DIR` | `./output` | Where rendered files land |
| `LOG_LEVEL` / `LOG_JSON` | `INFO` / `true` | Logging |
| `HOST` / `PORT` | `0.0.0.0` / `8080` | Bind |
| `TRANSLATION_TIMEOUT_S` | `15` | Per-translation request |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset | Optional OpenTelemetry tracing |

Missing custom paths fall back to the bundled samples with a structured warning log.

---

## Conventions for your own assets

See [`.github/instructions/templates.instructions.md`](.github/instructions/templates.instructions.md) and [`src/mcp_market_research/samples/README.md`](src/mcp_market_research/samples/README.md) for full details.

### Module workbook (preferred — drives the multi-agent flow)

One workbook with three sheet families:

- `core` — channel- and industry-agnostic core questions (~84 in production).
- `industry__<industry>` — industry-specific, channel-agnostic (~74 each). e.g. `industry__opticians`.
- `unique__<industry>__<channel>` — industry × channel unique questions (~6 each). e.g. `unique__opticians__social_media`.
- Sheets prefixed with `_` are skipped (use for author notes).

**Required columns** (case-insensitive header in row 1): `id` (unique across workbook, e.g. `core_001`), `section`, `question_text` (use `<COMPANY>`, `<PRODUCT>`, `<INDUSTRY>` placeholders), `question_type` ∈ `{single_choice, multi_choice, scale, open_text, numeric, yes_no, rating}`.

**Optional columns:** `options` (pipe-separated `|`), `required` (`yes|y|true|1|t`), `tags` (comma-separated, used for dedup/alignment), `notes` (not rendered).

### Legacy guidance workbook (single-agent fallback)

One sheet per channel; columns `section`, `question_type`, `guidance`, `example`, `required`, `notes`. Sheets prefixed `_` *and* sheets matching the module naming convention are skipped — so a single workbook can hold both shapes.

### PDF template

Placeholders match `{{KEY}}`. Reserved keys: `COMPANY_NAME`, `QUESTIONNAIRE_TITLE`, `LANGUAGE`, `COUNTRY`, `GENERATED_DATE`. Used as a *layout reference only*.

### DOCX template

docxtpl Jinja2 template — this is what actually renders. Variables: `{{ company_name }}`, `{{ questionnaire_title }}`, `{{ sections }}`, etc. RTL (`w:bidi`) is applied automatically for Arabic, Hebrew, Persian, and Urdu based on the `language` field.

---

## Production deployment

```powershell
docker compose up -d
```

Runs the FastMCP server + Caddy auto-TLS reverse proxy. Set your domain in `Caddyfile`.

See [`Dockerfile`](Dockerfile) and [`docker-compose.yml`](docker-compose.yml).

---

## Testing

```powershell
py -m pip install -e ".[dev]"
py -m pytest -q
```

Includes unit tests (parsers, renderer, translator), an integration test that produces a real `.docx`, and an MCP contract test.

---

## License

MIT
