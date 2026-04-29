---
name: idiomatic-translate
description: Method for translating an approved English questionnaire into a target language idiomatically — not literally — while preserving structure for the renderer.
---

# Skill: Idiomatic translation

Used by the **questionnaire-translator** agent.

## Principle

A native speaker reading the translated questionnaire should not be able to tell it was translated. Literal translations stink of MTL output and tank response quality. Idiomatic translations match the conventions of the target country's market research industry.

## The 4-pass method

### Pass 1: Plan

Before translating, decide:
- **Register** — formal (vous / Sie / keigo) vs informal (tu / du). For market research, **default to formal**. Only go informal if the brand explicitly targets youth / Gen Z and the source is informal.
- **Tone words** — e.g. "How likely are you to…" → French market research convention is "Dans quelle mesure seriez-vous susceptible de…", not the literal "Combien êtes-vous susceptible de…".
- **Country variant** — fr-FR vs fr-CA vs fr-BE differ. Pick based on `country_code`.

### Pass 2: Translate semantics, not words

For each string:
1. Read the English. Identify the *intent*, not the words.
2. Render the intent in the target language using local market-research conventions.
3. Compare back-translated meaning to the source. If they diverge, fix the target.

Worked example:
- EN: "How would you rate the quality of our service?"
- Bad (literal): "Comment évalueriez-vous la qualité de notre service ?"
- Good (idiomatic): "Comment jugez-vous la qualité de notre service ?" (French market research uses *juger* more often than *évaluer* in this context.)

### Pass 3: Country/locale fit

- **Currencies, units, dates** — convert presentation, not values, where appropriate. "$50/month" → "50 USD / mois" in French (keep USD, change format). Don't fabricate exchange rates.
- **Examples** — if a question references "the US market" or "American consumers", DO translate the country phrase but **don't auto-replace** with the target country (the user must approve a content change).
- **RTL languages (ar, he, fa, ur)** — translate normally; the renderer handles paragraph direction via `w:bidi`. Keep numerals as Arabic numerals (the renderer does not transform digits).
- **Honorifics / forms of address** — e.g., German "Sie" + capitalized "Ihr/Ihre". Japanese keigo. Korean nopimmal. Use the right register consistently throughout.

### Pass 4: Structure verification

Before returning the translated `RenderRequest`, verify:
- [ ] Same section count.
- [ ] Same question count per section.
- [ ] Same question types (don't change `single_choice` to `open_text` even if the target language renders it more naturally).
- [ ] Same options count per question.
- [ ] Same `required` flags.
- [ ] Same `extra_placeholders` keys (translate values that are user-facing prose).

If structure changed, you broke the contract — go back and fix before returning.

## Things never to translate

- Brand names ("Acme Corp" stays as is, even in non-Latin scripts unless the brand has an official localized name).
- Product SKUs, version numbers, IDs.
- URLs and email addresses.
- Numerical anchors in rating scales (the *labels* translate; the numbers don't).

## Fallback

If you're stuck on a phrase:
1. Call `translate_text_blocks` for *just that string*.
2. Read the output as a starting point.
3. **Always rewrite** for naturalness. Never ship the raw `translate_text_blocks` output verbatim — it's a baseline, not a deliverable.

## Quality bar

A native market-research professional reads the final document and finds it natural enough that they wouldn't ask for a re-translation. If you can't hit that bar in a language, tell the orchestrator and let the user decide whether to ship the deterministic translation as a fallback or skip the translation entirely.
