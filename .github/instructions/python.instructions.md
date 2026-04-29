---
applyTo: "src/**/*.py,tests/**/*.py,scripts/**/*.py"
---

# Python instructions

- **Python 3.11+.** Use modern syntax: `X | None`, `list[T]`, `dict[K, V]`, `str | Path`. Don't import from `typing` what's already a builtin generic.
- **Pydantic v2** for all data shapes — `BaseModel`, `Field`, `model_validator`. Don't reach for `dataclasses` or `TypedDict` for tool I/O.
- **Paths via `pathlib.Path`.** No `os.path.join`, no string-concat paths. Server runs on Windows in production.
- **FastMCP tool docstrings ship to Copilot as the tool description.** Keep them tight (1–3 lines), describe what the tool returns, not how it works.
- **`@traced_tool(name)`** decorator wraps every tool — apply it before `@app.tool()` so logs include `tool` + `duration_ms`.
- **Errors:** raise typed exceptions from [`errors.py`](../../src/mcp_market_research/errors.py). For Excel validation, include the sheet name and 1-based row index in the message.
- **No print().** Use `structlog.get_logger(__name__).info(...)` with kwargs.
- **Tests:** `pytest`, `pytest-asyncio`. Integration tests must produce a real `.docx` and assert it opens — don't mock the renderer.
- **No new dependencies** without updating [`pyproject.toml`](../../pyproject.toml).
- **No comments restating what the code does.** Only comment surprising constraints or workarounds.
