---
name: align-sections
description: Canonical section flow for market research questionnaires. Used by the composer agent to reorganize questions from the 3 modules into a coherent respondent-friendly structure.
---

# Skill: Align sections

Used by the **questionnaire-composer** agent after dedup.

## The canonical flow

Order matters. Respondent fatigue is real. Engaging questions first, demographics last.

| # | Section | Purpose | Length |
|---|---|---|---|
| 1 | **Screener / qualification** | Filter out non-target respondents fast. Single-choice or yes_no. | 1–3 questions |
| 2 | **Awareness & consideration** | Top-of-funnel: do they know the brand / category? | 3–6 |
| 3 | **Channel-specific behavior** | The unique module's questions land here mostly. | 4–8 |
| 4 | **Brand / product perception** | Attribute ratings, brand associations. | 5–10 |
| 5 | **Purchase / conversion** | Pricing sensitivity, decision criteria. | 4–8 |
| 6 | **Loyalty / NPS / retention** | Likelihood to recommend, repurchase intent. | 3–5 |
| 7 | **Open feedback** | One or two open_text questions. | 1–2 |
| 8 | **Demographics & consent** | Age, location, gender (optional), opt-in. | 3–6 |

Total target: **40–70 questions**.

## Re-tagging rules

The source modules use their own section names (e.g. `core` might have `Onboarding`, `Brand love`, `Perception`). You're allowed — required, even — to **regroup**.

- Take each question's `tags` and decide which canonical section it fits.
- If a question's original section name has no good canonical fit, look at the question text and tag set to place it.
- Don't keep an empty canonical section. If you have nothing for "Brand perception", drop the section header entirely.
- Don't keep a one-question section unless it's a screener or an open-text feedback prompt.

## Tag-to-section mapping (default)

| Tag | Section |
|---|---|
| `screener`, `qualification` | 1 |
| `awareness`, `consideration`, `top_of_funnel` | 2 |
| `behavior`, `usage`, `channel`, `frequency` | 3 |
| `perception`, `attribute`, `brand`, `quality` | 4 |
| `purchase`, `pricing`, `conversion`, `decision` | 5 |
| `nps`, `loyalty`, `referral`, `retention` | 6 |
| `feedback`, `open` | 7 |
| `demographic`, `consent`, `pii` | 8 |

A question with **no tags** goes by question type intuition: open_text → 7; rating → 4; single_choice with branching → 1 (probably a screener).

## Pacing rules

- **Don't open with rating grids.** Start with a quick 1-click question to get respondents committed.
- **Distribute open_text** — too many in a row kill response rate. Cap at 2 open_texts adjacent to each other.
- **Mix question types.** Rotate single_choice → rating → multi_choice → scale to keep the page visually varied.
- **Group by topic, not by type** — within a section, related questions should be adjacent regardless of question type.

## Required flag discipline

Only mark `required: true` when:
- It's a **screener** (and they need to qualify).
- It's a **legal consent** (e.g., GDPR opt-in for personal-data follow-up).
- The question's omission would invalidate the response.

Default to `required: false`. Surveys with too many required questions have higher abandonment.
