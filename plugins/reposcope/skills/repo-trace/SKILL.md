---
name: repo-trace
description: >
  Build a map of the repository: every source file ranked by token cost, plus
  git history, current branch, and the files changed in the last commit. Use
  when the user asks for a repo overview or project structure.
---

# Repo Trace

> Tier: Free. Repo Map is part of the free standalone RepoScope plugin and runs fully locally with no license or network.

## When to use

- User asks "what does this repo look like?" or "show me the project structure"
- When navigating an unfamiliar codebase for the first time
- To understand which files changed recently and why
- To see which files are the heaviest by token cost

## Instructions

1. Walk the workspace file tree, excluding common non-source directories (node_modules, .git, build outputs).
2. Gather git metadata: current branch, recent commits, files changed in the last commit.
3. Annotate each file with its token count from the Token Audit and rank files by token cost.
4. Present the result as a ranked file list — users should be able to click any file to open it.

## Output format

Return a structured tree with:
- `branch`: current git branch name
- `files`: array of `{ path, tokens, lastModified }` representing all source files
- `recentCommits`: array of `{ hash, message, author, date }` for the last 5 commits
- `changedFiles`: files modified in the most recent commit
