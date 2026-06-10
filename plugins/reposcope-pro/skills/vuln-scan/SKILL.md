---
name: vuln-scan
description: >
  Scan source code, a git diff, or a whole workspace for security issues using
  confidence-rated, CWE-tagged pattern heuristics. Detects committed secrets
  (cloud/API keys, JWTs, private keys, DB connection strings, .env values),
  injection (eval/SQL/command execution), XSS (innerHTML and framework sinks),
  insecure transport, weak crypto, and known-vulnerable dependencies — and
  returns a 0-100 security score. Use when the user asks about security,
  secrets, or vulnerabilities in their code.
---

# Vulnerability Scan

> Tier: Pro. Security is a RepoScope Pro feature. Requires a valid license — set `REPOSCOPE_LICENSE_KEY` (your Stripe customer id, `cus_…`) or add a `.reposcope-license` file to the workspace root. Without entitlement the skill returns a `pro_required` upsell instead of findings. Upgrade at https://reposcope.app/pricing.html.

## When to use

- User asks "are there any security issues?" or "scan for secrets"
- Before merging a pull request — check the diff for new vulnerabilities
- During a security audit or compliance review
- When onboarding to an unfamiliar codebase and need a security baseline

## Instructions

1. Accept a full workspace path, a single file, or a git diff as input.
2. Run pattern-based, confidence-rated checks (best-effort, not a full OWASP audit):
   - **Secrets (CWE-798):** API/cloud keys (GitHub, Slack, Google, Stripe), AWS keys, JWTs, private keys, hardcoded passwords, DB connection strings with embedded credentials, and secret-like values committed in `.env` files.
   - **Injection (CWE-78/89/95):** `eval()`, SQL string concatenation, and command execution (`os.system`, `subprocess(shell=True)`, `child_process` exec, `Runtime.exec`, `shell_exec`).
   - **XSS (CWE-79):** `innerHTML`/`outerHTML`, React `dangerouslySetInnerHTML`, Vue `v-html`, Angular `bypassSecurityTrust*`, `document.write`, `insertAdjacentHTML`.
   - **Misconfiguration:** permissive CORS (`Access-Control-Allow-Origin: *`, CWE-942), disabled TLS verification (`rejectUnauthorized: false`, `verify=False`, `InsecureSkipVerify`, CWE-295), and weak crypto (MD5/SHA-1, CWE-327).
   - **Dependencies (CWE-1104):** known-vulnerable npm/pip versions from an offline advisory list (`package.json`, `requirements.txt`).
3. Optionally merge Semgrep results when `reposcope.semgrepPath` is configured.
4. Flag severity (Critical/High/Medium/Low) and confidence (high/medium/low). Placeholder-looking values are down-weighted.
5. Respect suppression: skip files matching a `.reposcope-ignore` file (gitignore-style globs) and findings carrying an inline `// reposcope-ignore` comment (same line or the line above).
6. For each finding, include the file path, line number, CWE, and a concrete fix suggestion.

## Output format

Return a report:

```json
{
  "total": 12,
  "score": 64,
  "grade": "D",
  "critical": 1, "high": 3, "medium": 5, "low": 3,
  "scannedFiles": 240,
  "suppressed": 4,
  "byType": [{ "type": "env_secret", "count": 3, "severity": "high" }],
  "findings": [
    { "severity": "high", "confidence": "high", "cwe": "CWE-798",
      "type": "db_connection_creds", "file": "src/db.ts", "line": 14,
      "message": "...", "snippet": "...", "fix": "..." }
  ]
}
```

`findings` are sorted by severity descending. The 0-100 `score` weights each finding by severity and confidence (higher score = safer).
