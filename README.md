# questionaire

An MCP server that lets **Microsoft 365 Copilot Enterprise** agents generate market research questionnaires — in any language, for any country — driven by:

- a multi-sheet **Excel guide** (one sheet per channel),
- a **PDF layout reference** with `{{PLACEHOLDERS}}`,
- a **Word `.docx` template** that renders the final document.

The server is **structural, not generative**. Your Copilot agent's LLM composes the question text; this server provides deterministic tools (parse Excel, parse PDF, render DOCX, localize, translate).

> Designed for users with Copilot Enterprise but **no Azure subscription**. The Copilot agent's LLM does the creative work; this MCP server does the structural work.

---

## Architecture

```
Copilot Studio agent ──HTTPS──▶ Caddy (TLS) ──▶ FastMCP server (Streamable HTTP)
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

## Connecting to Microsoft 365 Copilot

### Path A — Copilot Studio (low-code, recommended)

1. Expose your server on a public HTTPS URL (Caddy + a domain, or `ngrok http 8080`).
2. Copilot Studio → **Tools** → **Add tool** → **Model Context Protocol**.
3. Server URL: `https://<your-host>/mcp`. Auth: **API key**, header `Authorization`, value `Bearer <your-key>`.
4. The wizard tests the connection and lists the 8 tools.
5. **Add to agent**, enable in topics.

### Path B — Microsoft 365 Agents Toolkit (declarative agent in VS Code)

1. VS Code → **Microsoft 365 Agents Toolkit** → **Create a New Agent/App** → **Declarative Agent** → **Add an Action** → **Start with an MCP Server**.
2. Paste your server URL.
3. Open `.vscode/mcp.json` → click **Start**, then **ATK: Fetch action from MCP** → select tools.
4. Choose **API key** auth (or OAuth static registration if you've configured an OAuth app).
5. **Provision** → **Sideload** → test at `https://m365.cloud.microsoft/chat`.

See [`deploy/copilot-studio-setup.md`](deploy/copilot-studio-setup.md) for the click-by-click walkthrough.

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
