---
name: repo-trace
description: >
  Build an interactive map of the repository structure. Shows the file tree
  with token density, git history, branch info, and dependency relationships.
  Use when the user asks for a repo overview, project structure, or
  dependency graph.
---

# Repo Trace

> Tier: Free. Repo Map is part of the free standalone RepoScope plugin and runs fully locally with no license or network.

## When to use

- User asks "what does this repo look like?" or "show me the project structure"
- When navigating an unfamiliar codebase for the first time
- To understand which files changed recently and why
- To visualize dependency relationships between modules

## Instructions

1. Walk the workspace file tree, excluding common non-source directories (node_modules, .git, build outputs).
2. Gather git metadata: current branch, recent commits, files changed in the last commit.
3. Build a dependency graph from import/require statements.
4. Annotate each file node with its token count from the Token Audit.
5. Present the tree as an interactive map — users should be able to click any file to open it.

## Output format

Return a structured tree with:
- `branch`: current git branch name
- `files`: array of `{ path, tokens, lastModified }` representing all source files
- `recentCommits`: array of `{ hash, message, author, date }` for the last 5 commits
- `changedFiles`: files modified in the most recent commit
