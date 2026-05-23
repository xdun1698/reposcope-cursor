import json
import os
import re
import sys
from pathlib import Path

from shared import TEXT_SUFFIXES, iter_text_files

SCAN_SKIP_SUFFIXES = frozenset({".md", ".json", ".xml", ".yaml", ".yml", ".txt"})
VULN_SCAN_SUFFIXES = frozenset(TEXT_SUFFIXES - SCAN_SKIP_SUFFIXES)

COMMENT_PREFIX_RE = re.compile(r"^\s*(//|#|/\*|\*|<!--)")

ENV_FALLBACK_RE = re.compile(
    r"(process\.env\.\w+|Environment\.GetEnvironmentVariable|os\.getenv|os\.environ|ENV\[|ENV\.fetch)"
)


def _is_commented(line: str) -> bool:
    return bool(COMMENT_PREFIX_RE.match(line))


def _is_env_fallback_url(line: str) -> bool:
    """Return True when a localhost URL appears as a fallback for an env variable."""
    return bool(ENV_FALLBACK_RE.search(line))


PATTERNS = {
    "api_key": r'(?i)\b(api[_-]?key|api[_-]?secret)\s*=\s*["\']([a-zA-Z0-9_\-]{8,})["\']',
    "aws_key": r"(?i)(AKIA|ASIA)[A-Z0-9]{16}",
    "prompt_injection": r"(?i)(ignore\s+previous|forget\s+all|override\s+system|(?<![a-zA-Z])system\s*:\s*)",
    "hardcoded_password": r'(?i)\b(password|passwd|pwd)\b\s*=\s*["\']([^"\']{4,})["\']',
    "hardcoded_url": r"(?i)https?://(localhost|127\.0\.0\.1)",
    "private_key": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
}

SEVERITY = {
    "api_key": "high",
    "aws_key": "critical",
    "prompt_injection": "medium",
    "hardcoded_password": "high",
    "hardcoded_url": "low",
    "private_key": "critical",
}

FIXES = {
    "api_key": "Move to env var: os.getenv('MY_API_KEY')",
    "aws_key": "Use IAM roles or AWS Secrets Manager — never hardcode",
    "prompt_injection": "Sanitize user input — escape or use allow-list validation",
    "hardcoded_password": "Use env vars or a secrets manager",
    "hardcoded_url": "Use config file or relative paths",
    "private_key": "Remove immediately — rotate this key, use secrets manager",
}

# Master-prompt heuristics (workspace scan)
WORKSPACE_RULE_TEXT: dict[str, tuple[str, str]] = {
    "hardcoded_secret": (
        "Possible hardcoded secret (e.g. API key or password) in source",
        "Move real credentials to environment variables or a secrets manager; do not commit secrets.",
    ),
    "eval_call": (
        "eval() is called with an expression — this can run arbitrary code",
        "Remove eval(); use JSON.parse, a vetted parser, or a safe alternative.",
    ),
    "sql_concat": (
        "SQL may be built with string formatting — injection risk if input is tainted",
        "Use parameterized queries, bound parameters, or an ORM; never paste user input into raw SQL strings.",
    ),
    "innerhtml_assign": (
        "DOM innerHTML is assigned directly — XSS risk if the value is influenced by user input",
        "Prefer textContent, a sanitizer, or your framework’s safe HTML APIs.",
    ),
}

WORKSPACE_RULES: list[tuple[str, str, str]] = [
    (
        "hardcoded_secret",
        "high",
        r"(?i)\b(api_key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]",
    ),
    # Match eval( with a non-empty argument; avoids prose like "eval() usage" in strings.
    ("eval_call", "critical", r"\beval\s*\(\s*(?!\s*\))"),
    ("sql_concat", "high", r"(?i)(execute|query|cursor)\s*\(\s*['\"][^'\"]*%\s*"),
    ("innerhtml_assign", "high", r"(?i)\.innerHTML\s*="),
]


def vuln_scan(input_data: dict) -> dict:
    code = input_data.get("code") or input_data.get("diff", "")
    if not code:
        return {"error": "No code provided"}

    findings = []
    lines = code.split("\n")
    for name, pattern in PATTERNS.items():
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line):
                findings.append(
                    {
                        "type": name,
                        "severity": SEVERITY[name],
                        "line": i,
                        "snippet": line.strip()[:100],
                        "fix": FIXES[name],
                        "message": FIXES[name],
                        "file": "",
                    }
                )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda x: severity_order.get(x["severity"], 9))
    urgent = sum(1 for f in findings if f["severity"] in ("critical", "high"))

    counts = _severity_counts(findings)

    return {
        "total": len(findings),
        "findings": findings[:5],
        "summary": f"{len(findings)} issues found — {urgent} urgent",
        **counts,
    }


def _severity_counts(findings: list[dict]) -> dict:
    c = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = str(f.get("severity", "low")).lower()
        if sev in c:
            c[sev] += 1
    return c


def vuln_scan_workspace(workspace_path: str) -> dict:
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return {"error": "workspacePath is not a directory"}

    findings: list[dict] = []

    for fp in iter_text_files(root, suffixes=VULN_SCAN_SUFFIXES):
        rel = str(fp.relative_to(root)).replace(os.sep, "/")
        try:
            lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        for rule, sev, pattern in WORKSPACE_RULES:
            rx = re.compile(pattern)
            for i, line in enumerate(lines, 1):
                if _is_commented(line):
                    continue
                if rx.search(line):
                    msg, ffix = WORKSPACE_RULE_TEXT.get(
                        rule,
                        (f"Suspicious pattern ({rule})", "Review and remove or refactor this line."),
                    )
                    findings.append(
                        {
                            "type": rule,
                            "severity": sev,
                            "line": i,
                            "file": rel,
                            "message": msg,
                            "snippet": line.strip()[:120],
                            "fix": ffix,
                        }
                    )

        for name, pattern in PATTERNS.items():
            rx = re.compile(pattern)
            for i, line in enumerate(lines, 1):
                if _is_commented(line):
                    continue
                if name == "hardcoded_url" and _is_env_fallback_url(line):
                    continue
                if rx.search(line):
                    findings.append(
                        {
                            "type": name,
                            "severity": SEVERITY[name],
                            "line": i,
                            "file": rel,
                            "message": FIXES[name],
                            "snippet": line.strip()[:120],
                            "fix": FIXES[name],
                        }
                    )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda x: severity_order.get(str(x.get("severity", "low")), 9))
    counts = _severity_counts(findings)
    urgent = counts["critical"] + counts["high"]

    return {
        "total": len(findings),
        "findings": findings[:50],
        "summary": f"{len(findings)} issues found — {urgent} urgent",
        **counts,
    }


def _main() -> None:
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        try:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = json.loads(Path(raw).read_text(encoding="utf-8"))
        except Exception:
            print(json.dumps({"error": "Invalid input"}))
            return
        if isinstance(data, dict) and (data.get("workspacePath") or data.get("workspaceRoot")):
            ws = str(data.get("workspacePath") or data.get("workspaceRoot") or "")
            print(json.dumps(vuln_scan_workspace(ws)))
            return
        print(json.dumps(vuln_scan(data if isinstance(data, dict) else {})))
        return

    try:
        raw_in = sys.stdin.read()
        if not raw_in.strip():
            print(json.dumps({"error": "stdin JSON required when no argv"}))
            return
        data = json.loads(raw_in)
    except json.JSONDecodeError:
        print(json.dumps({"error": "invalid stdin JSON"}))
        return

    if not isinstance(data, dict):
        print(json.dumps({"error": "stdin must be a JSON object"}))
        return

    ws = data.get("workspacePath") or data.get("workspaceRoot")
    if isinstance(ws, str) and ws.strip():
        print(json.dumps(vuln_scan_workspace(ws.strip())))
        return

    print(json.dumps(vuln_scan(data)))


if __name__ == "__main__":
    _main()
