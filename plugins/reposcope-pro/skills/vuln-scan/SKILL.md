---
name: vuln-scan
description: >
  Scan source code or a git diff for security vulnerabilities. Checks for
  OWASP Top 10 issues, hardcoded secrets, injection risks, and insecure
  dependencies. Use when the user asks about security, secrets, or
  vulnerabilities in their code.
---

# Vulnerability Scan

> Tier: Pro. Security is a RepoScope Pro feature. Requires a valid license — set `REPOSCOPE_LICENSE_KEY` (your Stripe customer id, `cus_…`) or add a `.reposcope-license` file to the workspace root. Without entitlement the skill returns a `pro_required` upsell instead of findings. Upgrade at https://reposcope.app/pricing.html.

## When to use

- User asks "are there any security issues?" or "scan for secrets"
- Before merging a pull request — check the diff for new vulnerabilities
- During a security audit or compliance review
- When onboarding to an unfamiliar codebase and need a security baseline

## Instructions

1. Accept either a full workspace path or a git diff as input.
2. Check for OWASP Top 10 vulnerabilities: injection, broken auth, sensitive data exposure, XXE, broken access control, misconfiguration, XSS, insecure deserialization, known vulnerable components, insufficient logging.
3. Scan for hardcoded secrets: API keys, tokens, passwords, connection strings.
4. Flag severity as Critical, High, Medium, or Low.
5. For each finding, include the file path, line number, and a concrete fix suggestion.

## Output format

Return findings as an array of `{ severity, type, file, line, message, fix }` sorted by severity descending.
