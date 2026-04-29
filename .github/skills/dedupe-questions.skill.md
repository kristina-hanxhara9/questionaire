---
name: dedupe-questions
description: Heuristic for resolving candidate duplicate questions across the core, industry, and unique modules. Apply when concatenating modules in the composer agent.
---

# Skill: Dedupe questions across modules

Used by the **questionnaire-composer** agent after calling `find_duplicate_candidates`.

## When to apply

The composer concatenates ~84 + ~74 + ~6 = ~164 questions. Many overlap. This skill defines how to resolve each candidate pair.

## The 4 outcomes

For every pair returned by `find_duplicate_candidates`:

### 1. KEEP BOTH

Different intent despite similar wording. Examples:
- "How likely are you to recommend us?" (NPS) vs "Would you recommend us to a colleague?" (B2B referral) — different audiences.
- "How satisfied are you with the product?" vs "How satisfied are you with the service?" — different objects.

Trigger: similarity ≥ 0.78 BUT tag overlap is small (< 2 tags) AND the objects/audiences differ on close reading.

### 2. MERGE

Same intent, slightly different wording. Pick the better-worded version. Fold any unique nuance from the other into the kept question's `notes`.

Pick winner by, in order:
1. **Specificity** — references the company / industry / channel concretely > generic.
2. **Brevity** — shorter is usually better in surveys.
3. **Module priority** — `unique` wins over `industry` wins over `core`. The more specific module won the right to phrase it.
4. **Tags** — the question with more tags has more cross-section utility; keep it.

### 3. DROP DUPLICATE

Strictly weaker version. The other question covers it completely.

### 4. SPLIT INTO TWO

Rare. Use when the "duplicate" is actually catching that the original was double-barreled. Both versions become two separate, narrower questions.

## Decision template

For each candidate, ask:
1. Do they have the same **research goal**? (If no → KEEP BOTH.)
2. Do they probe the same **construct** with the same **time frame** for the same **object**? (If yes → MERGE or DROP.)
3. Is one strictly weaker? (If yes → DROP. If no → MERGE.)

## Worked example

```
PrimaryID:   core_037   "How likely are you to recommend <COMPANY> to a friend?"
DuplicateID: opt_std_022 "Would you recommend our optician practice to family or friends?"
Tags overlap: [nps, referral, loyalty]
Similarity: 0.81
```

→ **MERGE.** Same construct (NPS-style referral). `opt_std_022` is more specific (says "optician practice"), so it wins. Drop `core_037`. Add note to `opt_std_022`: "Replaces core_037 NPS item."

## Reporting

When the composer hands off to the reviewer, include a JSON dedup log:

```json
{
  "merges": [{ "kept": "opt_std_022", "dropped": "core_037", "reason": "more specific" }],
  "drops":  [{ "id": "core_058", "reason": "covered by opt_std_011" }],
  "kept_both": [{ "ids": ["core_044", "opt_std_017"], "reason": "different audiences" }]
}
```

This lets the reviewer audit the dedup decisions, not just the final question list.
