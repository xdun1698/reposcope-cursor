---
name: suggest-goals
description: Generate 3-5 prioritized next goals from CodeWalker analysis results and current game plan.
---

# suggest-goals

You are helping prioritize work for the CodeWalker Cursor plugin.

Given the current `.cursor-plugin/plugin.json` manifest, Python skills under `skills/`, and any open Game Plan goals:

1. Read the repo context the user provides (or the active workspace summary).
2. Propose **3–5** next goals as numbered items in this exact format:

```
1. [Priority: High] Task: Short title
   Description: One or two sentences on scope and acceptance criteria.

2. [Priority: Medium] Task: ...
   Description: ...

Suggested additions complete.
```

3. Prefer goals that unblock marketplace readiness: tests passing, sidebar UX, licensing, and docs.

Do not invent secrets or URLs; keep tasks verifiable in-repo.
