---
name: token-audit
description: >
  Analyze token waste in the current workspace. Runs a lightweight AST parse
  to find unused imports, dead code, and bloated files that inflate LLM
  context cost. Use when the user asks about token counts, context budget,
  or which files are wasting tokens.
---

# Token Audit

## When to use

- User asks "which files are wasting tokens?" or "what's eating my context budget?"
- Before sending a large codebase to an LLM — identify files to exclude
- During code review to flag unnecessarily heavy files
- When optimizing a project for AI-assisted development

## Instructions

1. Run the Token Audit analysis on the workspace root.
2. Report the total token count and the top 5 heaviest files.
3. Flag unused imports and dead code blocks with estimated token savings.
4. Suggest specific files to exclude or refactor to reduce context cost.
5. Present results as a ranked table: file path, token count, waste category.

## Output format

Return a structured report with:
- `total_tokens`: aggregate BPE token count across all source files
- `top_files`: array of `{ file, tokens, waste_type }` sorted by token count descending
- `unused_imports`: count of removable import statements
- `dead_code`: count of unreachable code blocks
