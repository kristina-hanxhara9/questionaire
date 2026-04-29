---
mode: agent
description: Generate a market research questionnaire from the 3-module workbook (core + industry standard + channel-unique). Returns BOTH an English and a target-language .docx after composer / reviewer / translator pipeline.
agent: questionnaire-orchestrator
tools:
  - questionnaire/list_industries
  - questionnaire/list_channels_for_industry
  - questionnaire/list_supported_languages
  - questionnaire/get_country_locale
  - questionnaire/render_dual_language
---

# Generate questionnaire (multi-agent flow)

Hand this off to the **Questionnaire Orchestrator** agent. The orchestrator routes through the composer (assemble + dedup + align), reviewer (QA), and translator (idiomatic translation) before rendering both the English and target-language `.docx`.

## Inputs

- **Business:** ${input:business:Business name and 1-sentence description (industry, size, audience)}
- **Industry:** ${input:industry:Industry slug — must match one of list_industries (e.g. opticians)}
- **Channel:** ${input:channel:Channel slug — e.g. social_media, email, in_store}
- **Country:** ${input:country:ISO country code — e.g. US, FR, DE, AE} (default: US)
- **Language:** ${input:language:Target language — e.g. English, French, German, Arabic} (default: country's primary language)
- **Audience:** ${input:audience:Who responds — existing customers, prospects, lapsed users, employees…}

## What happens

1. **Orchestrator** validates inputs, calls `list_industries` and `list_channels_for_industry`.
2. **Composer** calls `assemble_modules`, dedupes via `find_duplicate_candidates`, aligns sections per the canonical flow, tailors questions to the business.
3. **Reviewer** runs the QA checklist; sends back blockers/fixes if any.
4. **Translator** produces an idiomatic target-language version (only if requested language ≠ English).
5. **Orchestrator** calls `render_dual_language` and returns both .docx files.

## Output

Two `.docx` files:
- `<title>_en_<timestamp>.docx`
- `<title>_<lang>_<timestamp>.docx` (only if the target language ≠ English)

Plus a one-paragraph summary of the research goals each section addresses.
