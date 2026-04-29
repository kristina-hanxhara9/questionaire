---
mode: agent
description: Generate a market research questionnaire for a specific business and channel, in any language and country. Renders a Word .docx via the questionnaire MCP server.
tools:
  - questionnaire/list_channels
  - questionnaire/get_channel_guide
  - questionnaire/list_supported_languages
  - questionnaire/get_country_locale
  - questionnaire/translate_text_blocks
  - questionnaire/render_questionnaire_docx
---

# Generate questionnaire

You are generating a market research questionnaire and rendering it as a Word `.docx` via the `questionnaire` MCP server.

## Inputs

- **Business:** ${input:business:Business name and 1-sentence description (industry, size, audience)}
- **Channel:** ${input:channel:Channel — e.g. social_media, email, in_store}
- **Language:** ${input:language:Target language — e.g. English, French, German, Arabic} (default: English)
- **Country:** ${input:country:ISO country code — e.g. US, FR, DE, AE} (default: US)
- **Audience:** ${input:audience:Who responds — existing customers, prospects, lapsed users, employees…}

## Steps

1. Call `list_channels`. If `${input:channel}` isn't an exact match, pick the closest and tell me what you chose.
2. Call `get_channel_guide(channel)` to retrieve sections, question types, and guidance.
3. Compose **5–15 questions per section**, tailored to the business above. Rewrite — don't copy the example fields. Use only the question types in the guide.
4. If the language isn't English, translate idiomatically. Use `get_country_locale` to pick the right date format and to detect RTL.
5. Call `render_questionnaire_docx` with the assembled `RenderRequest`. Set `extra_placeholders.QUESTIONNAIRE_TITLE` to a descriptive title.
6. Return the file path / filename / base64. Offer to revise any section.

## Output

A `.docx` file plus a one-paragraph summary of the research goals each section addresses.
