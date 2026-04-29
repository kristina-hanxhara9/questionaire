---
name: qa-review
description: QA checklist applied by the questionnaire-reviewer agent before approving an English RenderRequest for translation/render.
---

# Skill: QA review

Used by the **questionnaire-reviewer** agent.

## The checklist

Run through every item. Anything that fails goes into the `issues` array of the rejection response.

### Survey-design quality

| Check | Severity if violated |
|---|---|
| No double-barreled questions ("Are X and Y both important?") | blocker |
| No leading / loaded questions ("Don't you agree that…?") | blocker |
| Options for `single_choice` are mutually exclusive | blocker |
| Options for `multi_choice` cover the realistic option space (or include "Other") | fix |
| `rating` / `scale` endpoints are labeled (don't ship a 1–5 with no anchor text) | fix |
| Rating scale length is **consistent across the document** (one of 1–5 / 1–7 / 1–10, not mixed) | blocker |
| Each `single_choice` / `multi_choice` / `rating` question has `options`. | blocker |
| Numeric questions have a unit hint or implicit unit ("How many years…") | nit |
| At least one reverse-coded item to detect straight-lining (where the questionnaire has > 30 ratings) | nit |
| No PII traps (SSN, full DOB, government IDs) without explicit consent justification | blocker |
| No jargon the audience won't recognize | fix |
| Open-text prompts are specific ("What would improve X?" not "Comments?") | fix |

### Structural

| Check | Severity |
|---|---|
| Section flow follows canonical order (screener → … → demographics & consent) | fix |
| Demographics + consent sit **last** | blocker |
| Total question count is in **40–70** range | fix (flag if outside) |
| No empty sections, no single-question sections (except screeners / open feedback) | fix |
| All question IDs are unique | blocker |
| Consistent spelling of brand / product names across questions | nit |

### Template alignment

| Check | Severity |
|---|---|
| All non-reserved placeholders from `list_template_placeholders` are addressed (filled in `extra_placeholders` or noted intentionally blank) | fix |
| Reserved placeholders (`COMPANY_NAME`, `QUESTIONNAIRE_TITLE`, `LANGUAGE`, `COUNTRY`, `GENERATED_DATE`) are NOT manually overridden in `extra_placeholders` (renderer fills them) | nit |

### Dedup sanity

Run `find_duplicate_candidates(all_questions, similarity_threshold=0.85)`. Any pair returned at this threshold is a hard duplicate that survived composer dedup. Severity: **blocker**.

## Issue format

Each issue must have:

```json
{
  "severity": "blocker|fix|nit",
  "location": "section <N>, question <M>" or "global",
  "issue":   "<one sentence on what's wrong>",
  "fix":     "<one sentence on what to do>"
}
```

## Approve when

- No blockers.
- ≤ 3 fix-level issues (more than 3 fixes → reject).
- Any number of nits.

If approving with nits, include them in the summary so the composer can address them on a future pass.
