---
name: game-plan
description: >
  Manage the Reposcope Game Plan — a persistent task list stored in
  .reposcope-gameplan.json. Reads agent output and extracts actionable
  goals. Use when the user asks about goals, next steps, or wants to
  update their project plan from AI agent output.
---

# Game Plan

## When to use

- User asks "what should I work on next?" or "update my game plan"
- After an AI agent session — extract suggested goals from the output
- When reviewing analysis results and turning findings into tasks
- To track progress on security fixes, refactoring, or documentation

## Instructions

1. Read the existing `.reposcope-gameplan.json` from the workspace root (create if absent).
2. If agent output is provided, parse it for actionable goals.
3. Merge new goals with existing ones (deduplicate by task text).
4. Categorize goals: security, performance, refactor, test, docs, general.
5. For each goal, include a priority (high/medium/low) and affected files when identifiable.
6. Write the updated plan back to `.reposcope-gameplan.json`.

## Output format

Return the updated plan as:
- `project`: workspace name
- `goals`: array of `{ text, category, priority, status, files, fixHint }`
- `version`: schema version string
