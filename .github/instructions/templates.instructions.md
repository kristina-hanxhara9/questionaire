---
applyTo: "src/mcp_market_research/samples/**,assets/**,scripts/generate_samples.py"
---

# Template & sample asset instructions

- **Don't hand-edit binaries** in `src/mcp_market_research/samples/` (`sample_channel_guide.xlsx`, `sample_modules.xlsx`, `sample_template.pdf`, `sample_template.docx`). They are generated. Edit [`scripts/generate_samples.py`](../../scripts/generate_samples.py) and regenerate.
- **`assets/`** is gitignored except for `.gitkeep` and `README.md`. Real Excel/PDF/DOCX files belong there. Never commit real customer data.

## Module workbook (preferred)

Used by the multi-agent flow (orchestrator → composer → reviewer → translator).

**Sheet naming:**
- `core` — channel-agnostic, industry-agnostic core questions (~84 in production).
- `industry__<industry>` — industry-specific, channel-agnostic (~74 each). e.g. `industry__opticians`, `industry__dentists`.
- `unique__<industry>__<channel>` — industry × channel unique questions (~6 each). e.g. `unique__opticians__social_media`.
- Sheets prefixed with `_` (single underscore) are skipped — use for author notes.
- The case-insensitive naming uses **double underscore** as separator. Industry/channel slugs themselves should be lowercase + underscore.

**Required columns** (case-insensitive header in row 1):
- `id` — stable question ID (e.g. `core_001`, `opt_std_023`, `opt_sm_004`). Must be unique across the entire workbook.
- `section` — section name within the module (the composer will regroup into canonical sections).
- `question_text` — the actual question text (use `<COMPANY>`, `<PRODUCT>`, `<INDUSTRY>` placeholders that the composer fills inline).
- `question_type` ∈ `{single_choice, multi_choice, scale, open_text, numeric, yes_no, rating}`.

**Optional columns:**
- `options` — pipe-separated (`|`) values for single/multi/rating types.
- `required` — truthy values: `yes`, `y`, `true`, `1`, `t`.
- `tags` — comma-separated topical tags used for dedup/alignment (e.g. `awareness,top_of_funnel`).
- `notes` — author notes; not rendered.

## Legacy guidance workbook

Used by the older single-agent flow. Kept for backwards compatibility.

- One sheet per channel. Sheet name == channel name.
- Header row 1: `section`, `question_type`, `guidance`, `example`, `required`, `notes` (optional). Case-insensitive.
- Same `question_type` vocabulary as above.
- Sheets prefixed with `_` are skipped, AND any sheet matching the module naming convention (`core`, `industry__*`, `unique__*`) is skipped — so a single workbook can hold both types if needed.

## PDF template

- Placeholders match `{{KEY}}` where KEY is `[A-Z][A-Z0-9_]+`.
- Reserved: `COMPANY_NAME`, `QUESTIONNAIRE_TITLE`, `LANGUAGE`, `COUNTRY`, `GENERATED_DATE`.
- The PDF is a **layout reference only**; the DOCX is the actual render source.

## DOCX template

- Uses Jinja2 via docxtpl.
- Variables: `{{ company_name }}`, `{{ questionnaire_title }}`, `{{ sections }}`, etc.
- The renderer also handles RTL (`w:bidi`) for Arabic, Hebrew, Persian, Urdu based on the `language` field in `RenderRequest`.
