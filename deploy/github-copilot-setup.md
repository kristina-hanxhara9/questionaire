# Connecting the Questionnaire MCP server to GitHub Copilot

GitHub Copilot can call this MCP server from three places. Path A (VS Code chat) is the fastest to verify. Path B (cloud coding agent) lets the agent use the server during repo tasks. Path C (custom agent) gives you a one-click "Questionnaire Generator" persona.

---

## Prerequisites

- The MCP server is running and reachable.
  - **Local dev:** `python -m mcp_market_research` exposes `http://localhost:8080/mcp`.
  - **Production:** a public HTTPS URL such as `https://research-mcp.example.com/mcp` (Docker + Caddy auto-TLS — see [`docker-compose.yml`](../docker-compose.yml)).
- You know one of the values in `MCP_API_KEYS`.
- Your GitHub user / org has **Copilot** enabled (Business or Enterprise). MCP support is GA in VS Code Copilot.
- VS Code 1.99+ with the **GitHub Copilot** and **GitHub Copilot Chat** extensions.

---

## Path A — VS Code Copilot Chat (recommended first)

The repo ships [`.vscode/mcp.json`](../.vscode/mcp.json) with the server pre-wired. Open it once to confirm.

1. Open the repo in VS Code.
2. Run **MCP: List Servers** from the Command Palette → pick **questionnaire** → **Start Server**. VS Code prompts for:
   - **Server URL** — `http://localhost:8080/mcp` (local) or your production HTTPS URL.
   - **Bearer token** — one of your `MCP_API_KEYS` values. Stored in VS Code's secret storage; not written to disk.
3. Open **Copilot Chat** → switch to **Agent** mode (the dropdown next to the model picker).
4. Click the **tools** icon in the chat input. Confirm all 8 questionnaire tools are checked:
   - `list_channels`, `get_channel_guide`, `get_template_structure`, `list_template_placeholders`, `list_supported_languages`, `get_country_locale`, `translate_text_blocks`, `render_questionnaire_docx`.
5. Try a prompt:

   > Generate a social media questionnaire for Acme Corp, a coffee subscription brand, in English.

   Copilot should call `list_channels` → `get_channel_guide` → `render_questionnaire_docx` and return a `.docx` path.

### Reusable prompt

Run [`.github/prompts/generate-questionnaire.prompt.md`](../.github/prompts/generate-questionnaire.prompt.md) from the chat input (`/generate-questionnaire`) to get a guided form for business / channel / language / country.

### Custom agent

Select the **Questionnaire Generator** agent (defined in [`.github/agents/questionnaire-generator.agent.md`](../.github/agents/questionnaire-generator.agent.md)) from the chat persona dropdown. The agent ships with the workflow baked in — no need to re-explain every time.

---

## Path B — GitHub Copilot Cloud Coding Agent

This lets the cloud agent (the one that opens PRs from issues) call the questionnaire server during repo tasks — useful when you ask it to "regenerate the German variant of the survey".

1. Deploy the server to a public HTTPS URL (see [Production deployment](#production-deployment)).
2. In your GitHub repo: **Settings** → **Code & automation** → **Copilot** → **Coding agent**.
3. Find the **Model Context Protocol** section → **Add server**.
4. Fill in:
   - **Name:** `questionnaire`
   - **Type:** `http`
   - **URL:** `https://research-mcp.example.com/mcp`
   - **Headers:** `Authorization: Bearer <your-key>` (use repo or org secrets — do not paste plaintext).
5. **Save**. The agent now sees the 8 tools when it runs.
6. The cloud agent reads [`AGENTS.md`](../AGENTS.md) for repo conventions automatically.

---

## Path C — Other Copilot-compatible clients

The server speaks standard MCP over Streamable HTTP, so the same URL + bearer token works in:

- **Claude Code / Claude Desktop** — add to `~/.claude/mcp_servers.json` (or via `/mcp` slash command).
- **Cursor** — `Settings → MCP → Add server`.
- **Any FastMCP / official SDK client** — `MCPClient(url, headers={"Authorization": f"Bearer {key}"})`.

You don't need separate manifests; `.vscode/mcp.json` is VS-Code-specific and other clients have their own equivalent.

---

## Production deployment

```powershell
# Windows / PowerShell on the deploy host
docker compose up -d --build
```

The compose stack runs:
- `mcp` — the FastMCP server on port 8080 (internal).
- `caddy` — TLS termination + reverse proxy.

Edit [`Caddyfile`](../Caddyfile) to set your real hostname, then point DNS at the host. Caddy fetches a Let's Encrypt cert on first request.

To rotate keys: edit `MCP_API_KEYS` in `.env` (comma-separated) and `docker compose up -d`. Old keys keep working until removed.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `MCP: List Servers` shows nothing | Workspace not trusted | VS Code → **Restricted Mode** banner → **Manage Workspace Trust** |
| `401 Unauthorized` from server | Wrong key or header | Confirm `Authorization: Bearer <key>` matches one of `MCP_API_KEYS` |
| `Cannot connect` | Server not reachable | `curl <url>/healthz` from the same machine; check Docker logs: `docker compose logs mcp` |
| Tools list is empty in Copilot | Server failed to register tools | Check server logs for `tool_registration_error` |
| Cloud agent doesn't call the tools | MCP server misconfigured in repo settings | Re-check **Settings → Copilot → Coding agent → MCP** entry |
| Generated `.docx` is empty / missing fields | Wrong placeholder names in DOCX template | Run `list_template_placeholders` and align template tokens |
| Translations time out | `TRANSLATION_TIMEOUT_S` too low | Raise to `30` in `.env`, or have Copilot translate idiomatically without the tool |
| Sample-asset warnings on startup | `EXCEL_GUIDE_PATH` / `PDF_TEMPLATE_PATH` / `DOCX_TEMPLATE_PATH` not pointed at real files | Drop your files into [`assets/`](../assets/README.md) and update `.env` |

---

## Updating the server

After editing the Excel/PDF/DOCX or the server code:

```powershell
docker compose up -d --build
```

VS Code Copilot picks up new tool schemas on the next chat turn. The cloud agent picks them up on its next run. URL + key don't change.

If you **add or rename a tool**, also update:
- [`.github/agents/questionnaire-generator.agent.md`](../.github/agents/questionnaire-generator.agent.md) — `tools:` list.
- [`.github/prompts/generate-questionnaire.prompt.md`](../.github/prompts/generate-questionnaire.prompt.md) — `tools:` list.
- [`README.md`](../README.md) — tool catalog.
