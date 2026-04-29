---
applyTo: "src/mcp_market_research/samples/**,assets/**,scripts/generate_samples.py"
---

# Template & sample asset instructions

- **Don't hand-edit binaries** in `src/mcp_market_research/samples/` (`sample_channel_guide.xlsx`, `sample_template.pdf`, `sample_template.docx`). They are generated. Edit [`scripts/generate_samples.py`](../../scripts/generate_samples.py) and regenerate.
- **`assets/`** is gitignored except for `.gitkeep` and `README.md`. Real Excel/PDF/DOCX files belong there. Never commit real customer data.
- **Excel guide sheet shape:**
  - One sheet per channel. Sheet name == channel name.
  - Header row 1: `section`, `question_type`, `guidance`, `example`, `required`, `notes` (optional). Case-insensitive.
  - `question_type` ∈ `{single_choice, multi_choice, scale, open_text, numeric, yes_no, rating}`.
  - Sheets prefixed with `_` are skipped (use them for author notes).
- **PDF placeholders:** must match `{{KEY}}` where KEY is `[A-Z][A-Z0-9_]+`. Reserved: `COMPANY_NAME`, `QUESTIONNAIRE_TITLE`, `LANGUAGE`, `COUNTRY`, `GENERATED_DATE`.
- **DOCX template** uses Jinja2 via docxtpl. The PDF is a layout reference; the DOCX is the actual render source.
