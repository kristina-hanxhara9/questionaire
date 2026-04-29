# questionaire

An MCP server that lets **GitHub Copilot** agents generate market research questionnaires — in any language, for any country — driven by:

- a multi-sheet **Excel guide** (one sheet per channel),
- a **PDF layout reference** with `{{PLACEHOLDERS}}`,
- a **Word `.docx` template** that renders the final document.

The server is **structural, not generative**. The Copilot agent's LLM composes the question text; this server provides deterministic tools (parse Excel, parse PDF, render DOCX, localize, translate).

> Designed for users with GitHub Copilot Business / Enterprise but **no Azure subscription**. Copilot's LLM does the creative work; this MCP server does the structural work.

The repo ships first-class GitHub Copilot integration:

- [`.vscode/mcp.json`](.vscode/mcp.json) — VS Code Copilot picks up the server automatically.
- [`.github/agents/questionnaire-generator.agent.md`](.github/agents/questionnaire-generator.agent.md) — a custom **Questionnaire Generator** agent.
- [`.github/prompts/generate-questionnaire.prompt.md`](.github/prompts/generate-questionnaire.prompt.md) — reusable `/generate-questionnaire` prompt.
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — workspace context for Copilot.
- [`AGENTS.md`](AGENTS.md) — instructions for the GitHub Copilot **cloud coding agent**.

---

## Architecture

```
GitHub Copilot (VS Code or Cloud Agent) ──HTTPS──▶ Caddy (TLS) ──▶ FastMCP server (Streamable HTTP)
                                                                        │
                                                                        ├─ openpyxl     → channel guide
                                                                        ├─ pdfplumber   → template structure
                                                                        ├─ docxtpl      → DOCX render
                                                                        ├─ deep-translator → translation
                                                                        └─ Babel        → localization
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

## MCP tools (8 total)

| Tool | Purpose |
|---|---|
| `list_channels()` | Sheet names from the Excel guide |
| `get_channel_guide(channel)` | Sections, question types, guidance, examples, required flags |
| `get_template_structure()` | PDF section headings + placeholders |
| `list_template_placeholders()` | All `{{KEY}}` tokens with hints |
| `list_supported_languages()` | ISO codes + native names |
| `get_country_locale(country, language?)` | Date format, decimal separator, RTL flag |
| `translate_text_blocks(blocks, target, source="en")` | Deterministic translation via deep-translator |
| `render_questionnaire_docx(payload)` | Render final `.docx` and return path + base64 |

The Copilot LLM calls these in sequence: discover channels → fetch guidance → compose questions → render.

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

See [`src/mcp_market_research/samples/README.md`](src/mcp_market_research/samples/README.md) for full details.

**Excel guide:** one sheet per channel; columns `section`, `question_type`, `guidance`, `example`, `required`, `notes`. Sheets prefixed `_` are skipped.

**PDF template:** placeholders match `{{KEY}}`. Reserved keys: `COMPANY_NAME`, `QUESTIONNAIRE_TITLE`, `LANGUAGE`, `COUNTRY`, `GENERATED_DATE`. Used as a *layout reference only*.

**DOCX template:** docxtpl Jinja2 template — this is what actually renders. Variables: `{{ company_name }}`, `{{ questionnaire_title }}`, `{{ sections }}`, etc.

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
