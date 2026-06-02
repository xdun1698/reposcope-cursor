---
name: suggest-goals
description: >
  Generate 3-5 smart next goals for a repository based on Reposcope
  analysis results. Combines token waste, security findings, and repo
  structure to prioritize actionable improvements. Use when the user
  asks for goal suggestions or "what should I fix first?"
---

# Suggest Goals

> Tier: Pro. Suggested goals is a RepoScope Pro feature (paired with Game Plan). Requires a valid license — set `REPOSCOPE_LICENSE_KEY` (your Stripe customer id, `cus_…`) or add a `.reposcope-license` file to the workspace root. Without entitlement the skill returns a `pro_required` upsell. Upgrade at https://reposcope.app/pricing.html.

## When to use

- User clicks "Suggest Goals" in the Reposcope sidebar
- User asks "what should I work on?" or "prioritize my tasks"
- After running a full analysis — turn findings into a prioritized action list
- When onboarding to a new codebase and need a starting roadmap

## Instructions

1. Gather context from the latest Reposcope analysis: token waste report, security findings, repo map.
2. Identify the highest-impact improvements across all categories.
3. Propose 3-5 goals in priority order (High > Medium > Low).
4. For each goal, include:
   - A clear, actionable task title
   - One or two sentences of scope and acceptance criteria
   - The category (security, performance, refactor, test, docs)
   - Affected files when identifiable
5. Prefer goals that are verifiable in-repo — do not invent URLs or secrets.

## Output format

Return goals as an array of:
```
{ text, category, priority, description, files }
```
