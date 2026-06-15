"""Pattern-based security scanner (Phase 3).

Confidence-rated, CWE-tagged heuristics for secrets, injection, XSS, command
execution, insecure transport, weak crypto, committed env values, and
known-vulnerable dependencies. Produces a 0-100 security score. Kept in sync
with the TypeScript engine (`src/engine/vulnScanRegex.ts` + `vulnRules.ts`) for
identical JSON output on the same inputs.
"""

import json
import os
import re
import sys
from pathlib import Path

from shared import TEXT_SUFFIXES, SKIP_DIR_NAMES, MAX_WALK_FILES, MAX_FILE_BYTES

SCAN_SKIP_SUFFIXES = frozenset({".md", ".json", ".xml", ".yaml", ".yml", ".txt"})
VULN_SCAN_SUFFIXES = frozenset(TEXT_SUFFIXES - SCAN_SKIP_SUFFIXES)

MANIFEST_FILES = frozenset({"package.json", "requirements.txt", "requirements.in"})
WORKSPACE_FINDING_CAP = 1000

COMMENT_PREFIX_RE = re.compile(r"^\s*(//|#|/\*|\*|<!--)")

ENV_FALLBACK_RE = re.compile(
    r"(process\.env\.\w+|Environment\.GetEnvironmentVariable|os\.getenv|os\.environ|getenv\s*\(|std::getenv|System\.getenv|ENV\[|ENV\.fetch)"
)

PLACEHOLDER_RE = re.compile(
    r"(your[_-]?|example|placeholder|change[_-]?me|dummy|sample|redacted|xxxx|<[^>]+>|\*{3,}|todo|replace[_-]?this|insert[_-]?|foobar|abc123|123456)",
    re.IGNORECASE,
)


def _is_commented(line: str) -> bool:
    return bool(COMMENT_PREFIX_RE.match(line))


def _is_env_fallback_url(line: str) -> bool:
    return bool(ENV_FALLBACK_RE.search(line))


def _looks_like_placeholder(line: str) -> bool:
    return bool(PLACEHOLDER_RE.search(line))


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

CONFIDENCE = {
    "api_key": "high",
    "aws_key": "high",
    "prompt_injection": "low",
    "hardcoded_password": "medium",
    "hardcoded_url": "low",
    "private_key": "high",
    "hardcoded_secret": "medium",
    "eval_call": "high",
    "sql_concat": "medium",
    "innerhtml_assign": "medium",
}

CWE = {
    "api_key": "CWE-798",
    "aws_key": "CWE-798",
    "prompt_injection": "CWE-77",
    "hardcoded_password": "CWE-259",
    "hardcoded_url": "CWE-547",
    "private_key": "CWE-798",
    "hardcoded_secret": "CWE-798",
    "eval_call": "CWE-95",
    "sql_concat": "CWE-89",
    "innerhtml_assign": "CWE-79",
}

FIXES = {
    "api_key": "Move to env var: os.getenv('MY_API_KEY')",
    "aws_key": "Use IAM roles or AWS Secrets Manager — never hardcode",
    "prompt_injection": "Sanitize user input — escape or use allow-list validation",
    "hardcoded_password": "Use env vars or a secrets manager",
    "hardcoded_url": "Use config file or relative paths",
    "private_key": "Remove immediately — rotate this key, use secrets manager",
}

WORKSPACE_RULE_TEXT = {
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

WORKSPACE_RULES = [
    ("hardcoded_secret", "high", r"(?i)\b(api_key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
    ("eval_call", "critical", r"\beval\s*\(\s*(?!\s*\))"),
    ("sql_concat", "high", r"(?i)(execute|query|cursor)\s*\(\s*['\"][^'\"]*%\s*"),
    ("innerhtml_assign", "high", r"(?i)\.innerHTML\s*="),
]

# Phase 3 extended rules: (id, severity, confidence, pattern, message, fix, cwe, placeholder_aware)
EXTENDED_RULES = [
    ("jwt_token", "high", "medium", r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{6,}",
     "Hardcoded JWT detected — a signed token is embedded in source",
     "Never commit signed tokens; issue them at runtime and store secrets in a vault.", "CWE-798", False),
    ("github_token", "critical", "high", r"\bgh[pousr]_[A-Za-z0-9]{20,}",
     "GitHub personal/OAuth token committed in source",
     "Revoke the token immediately and move it to an environment variable or secret store.", "CWE-798", False),
    ("slack_token", "critical", "high", r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
     "Slack token committed in source",
     "Revoke the Slack token and load it from configuration at runtime.", "CWE-798", False),
    ("google_api_key", "high", "high", r"\bAIza[0-9A-Za-z_-]{35}\b",
     "Google API key committed in source",
     "Restrict and rotate the key; load it from an environment variable.", "CWE-798", False),
    ("stripe_secret_key", "critical", "high", r"\b(sk|rk)_live_[0-9a-zA-Z]{16,}",
     "Stripe LIVE secret key committed in source",
     "Roll the key in the Stripe dashboard now and read it from a secret store.", "CWE-798", True),
    ("stripe_test_key", "high", "medium", r"\b(sk|rk)_test_[0-9a-zA-Z]{16,}",
     "Stripe test secret key committed in source",
     "Even test keys should come from configuration, not source.", "CWE-798", True),
    ("slack_webhook", "high", "high", r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+",
     "Slack incoming webhook URL committed in source",
     "Treat webhook URLs as secrets; load from configuration.", "CWE-798", False),
    ("bearer_token", "medium", "medium", r"(?i)\bauthorization\s*[:=]\s*[\"']?\s*bearer\s+[A-Za-z0-9._-]{12,}",
     "Hardcoded Bearer authorization token",
     "Inject auth tokens at runtime; never hardcode them.", "CWE-798", True),
    ("db_connection_creds", "high", "high",
     r"(?i)\b(mongodb(\+srv)?|postgres(ql)?|mysql|mariadb|redis|amqps?)://[^\s:'\"@/]+:[^\s'\"@/]+@",
     "Database connection string with embedded username/password",
     "Move credentials out of the URI; use env vars or a secrets manager.", "CWE-798", True),
    ("sqlserver_connection_password", "high", "medium",
     r"(?i)(server|data source)\s*=[^;'\"]+;[^'\"]*\b(password|pwd)\s*=\s*[^;\s'\"]+",
     "SQL Server connection string with an inline password",
     "Use integrated auth or pull the password from configuration.", "CWE-798", True),
    ("cmd_os_system", "high", "medium", r"\bos\.system\s*\(",
     "os.system() shells out — command injection risk with dynamic input",
     "Use subprocess.run([...], shell=False) with an argument list.", "CWE-78", False),
    ("cmd_subprocess_shell", "high", "high", r"\bsubprocess\.\w+\([^)]*shell\s*=\s*True",
     "subprocess called with shell=True — command injection risk",
     "Pass an argument list and keep shell=False; never interpolate user input.", "CWE-78", False),
    ("cmd_popen", "medium", "low", r"\b(os\.popen|proc_open)\s*\(",
     "popen-style shell execution — review for injectable input",
     "Prefer an argument-list API without a shell; validate any dynamic input.", "CWE-78", False),
    ("cmd_php_shell", "high", "high", r"\b(shell_exec|passthru)\s*\(",
     "PHP shell execution function — command injection risk",
     "Avoid shell_exec/passthru; use escapeshellarg() and validated allow-lists.", "CWE-78", False),
    ("cmd_node_exec", "high", "medium",
     r"\bexecSync\s*\(|\bexec\s*\(\s*[`'\"][^`'\"]*(\$\{|\"\s*\+|'\s*\+|`\s*\+)",
     "child_process exec with a shell string — command injection risk",
     "Use execFile/spawn with an argument array; do not build shell strings.", "CWE-78", False),
    ("cmd_runtime_exec", "high", "medium", r"Runtime\.getRuntime\(\)\.exec\s*\(|new\s+ProcessBuilder\s*\(",
     "Java runtime command execution — command injection risk",
     "Pass arguments as an array and validate input; avoid concatenated commands.", "CWE-78", False),
    ("cmd_go_exec", "medium", "low", r'\bexec\.Command\s*\(\s*"(sh|bash|cmd|powershell)"',
     "Go exec.Command spawning a shell — command injection risk",
     "Invoke the target binary directly with explicit args instead of a shell.", "CWE-78", False),
    ("cmd_ruby_backtick", "high", "medium", r"`[^`]*#\{[^`]*`",
     "Ruby backtick command with string interpolation — command injection risk",
     "Use system([...]) / Open3 with an argument array, never interpolated backticks.", "CWE-78", False),
    ("react_dangerous_html", "high", "medium", r"dangerouslySetInnerHTML",
     "React dangerouslySetInnerHTML — XSS risk if the value is user-influenced",
     "Render text, or sanitize HTML (e.g. DOMPurify) before injecting it.", "CWE-79", False),
    ("vue_v_html", "medium", "medium", r"\bv-html\s*=",
     "Vue v-html binding — XSS risk if the value is user-influenced",
     "Prefer text interpolation, or sanitize before binding v-html.", "CWE-79", False),
    ("angular_bypass_security", "high", "high", r"bypassSecurityTrust\w*\s*\(",
     "Angular bypassSecurityTrust* disables built-in sanitization",
     "Avoid bypassing the sanitizer; sanitize untrusted values instead.", "CWE-79", False),
    ("document_write", "medium", "low", r"\bdocument\.write(ln)?\s*\(",
     "document.write() — XSS risk if the argument is user-influenced",
     "Build DOM nodes / use textContent instead of document.write.", "CWE-79", False),
    ("insert_adjacent_html", "medium", "low", r"insertAdjacentHTML\s*\(",
     "insertAdjacentHTML — XSS risk if the markup is user-influenced",
     "Insert text nodes or sanitize the HTML before insertion.", "CWE-79", False),
    ("outer_html_assign", "high", "medium", r"\.outerHTML\s*=",
     "outerHTML assigned directly — XSS risk if the value is user-influenced",
     "Prefer textContent or a sanitizer; avoid assigning raw HTML.", "CWE-79", False),
    ("cors_wildcard_header", "medium", "medium", r"(?i)access-control-allow-origin[\"']?\s*[:,]\s*[\"']\*[\"']",
     "CORS Access-Control-Allow-Origin set to \"*\"",
     "Restrict to an explicit allow-list of trusted origins.", "CWE-942", False),
    ("cors_lib_wildcard", "medium", "medium", r"(?i)\bcors\s*\(\s*\{[^}]*origin\s*:\s*([\"']\*[\"']|true)",
     "CORS middleware allows any origin",
     "Set origin to an explicit list; avoid \"*\" / true with credentials.", "CWE-942", False),
    ("tls_reject_unauthorized_false", "high", "high", r"(?i)rejectUnauthorized\s*:\s*false",
     "TLS certificate validation disabled (rejectUnauthorized: false)",
     "Keep certificate validation on; install proper CA certs instead.", "CWE-295", False),
    ("tls_node_env_disable", "high", "high", r"NODE_TLS_REJECT_UNAUTHORIZED\s*[:=]\s*[\"']?0",
     "NODE_TLS_REJECT_UNAUTHORIZED=0 disables all TLS verification",
     "Never disable global TLS verification; fix the certificate chain.", "CWE-295", False),
    ("tls_python_verify_false", "medium", "medium", r"\bverify\s*=\s*False\b",
     "TLS verification disabled (verify=False)",
     "Leave verify=True; provide a CA bundle if needed.", "CWE-295", False),
    ("tls_go_insecure_skip_verify", "high", "high", r"InsecureSkipVerify\s*:\s*true",
     "Go TLS InsecureSkipVerify: true disables certificate validation",
     "Remove InsecureSkipVerify; validate the server certificate.", "CWE-295", False),
    ("weak_hash_md5", "medium", "low",
     r"hashlib\.md5\b|createHash\(\s*[\"']md5[\"']\)|MessageDigest\.getInstance\(\s*[\"']MD5[\"']\)|\bMD5CryptoServiceProvider\b",
     "MD5 is cryptographically broken for security use",
     "Use SHA-256+ (hashing) or bcrypt/argon2/scrypt (passwords).", "CWE-327", False),
    ("weak_hash_sha1", "low", "low",
     r"hashlib\.sha1\b|createHash\(\s*[\"']sha1[\"']\)|MessageDigest\.getInstance\(\s*[\"']SHA-?1[\"']\)",
     "SHA-1 is deprecated for security use", "Use SHA-256 or stronger.", "CWE-327", False),
]

_EXTENDED_COMPILED = [
    (rid, sev, conf, re.compile(pat), msg, fix, cwe, ph)
    for (rid, sev, conf, pat, msg, fix, cwe, ph) in EXTENDED_RULES
]

SEVERITY_PENALTY = {"critical": 28, "high": 14, "medium": 5, "low": 1.5}
CONFIDENCE_FACTOR = {"high": 1.0, "medium": 0.65, "low": 0.35}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}


def _scan_line_extended(line: str, line_no: int, rel_file: str) -> list:
    out = []
    for rid, sev, conf, rx, msg, fix, cwe, placeholder_aware in _EXTENDED_COMPILED:
        if not rx.search(line):
            continue
        c = "low" if (placeholder_aware and _looks_like_placeholder(line)) else conf
        out.append({
            "type": rid,
            "severity": sev,
            "confidence": c,
            "line": line_no,
            "file": rel_file,
            "message": msg,
            "snippet": line.strip()[:120],
            "fix": fix,
            "cwe": cwe,
        })
    return out


# --- env file + dependency advisories ---------------------------------------

ENV_SECRET_KEY_RE = re.compile(
    r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|PWD|CREDENTIAL|PRIVATE|API|AUTH|ACCESS|DSN|DATABASE_URL|CONN)",
    re.IGNORECASE,
)
ENV_VALUE_REFERENCE_RE = re.compile(r"^\$\{?[A-Za-z_]")


def _is_env_file(name: str) -> bool:
    base = name.replace("\\", "/").split("/")[-1]
    if re.search(r"\.(example|sample|template|dist)$", base, re.IGNORECASE):
        return False
    return bool(re.match(r"^\.env(\.[A-Za-z0-9_-]+)?$", base))


def _scan_env_file(lines: list, rel_file: str) -> list:
    findings = []
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = re.sub(r"^export\s+", "", key, flags=re.IGNORECASE).strip()
        value = value.strip()
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        else:
            value = re.split(r"\s+#", value)[0].strip()
        if not value or ENV_VALUE_REFERENCE_RE.match(value):
            continue
        if not ENV_SECRET_KEY_RE.search(key) or len(value) < 6:
            continue
        placeholder = _looks_like_placeholder(value) or re.match(
            r"^(true|false|0|1|localhost|null|none)$", value, re.IGNORECASE
        )
        findings.append({
            "type": "env_secret",
            "severity": "high",
            "confidence": "low" if placeholder else "medium",
            "line": i,
            "file": rel_file,
            "message": f"Secret-like value committed in env file ({key})",
            "snippet": f"{key}=********",
            "fix": "Keep secrets out of committed env files; use .env.example with blanks and load real values from a secret store.",
            "cwe": "CWE-798",
        })
    return findings


NPM_ADVISORIES = {
    "event-stream": {"eq": "3.3.6", "severity": "critical", "note": "malicious flatmap-stream payload"},
    "lodash": {"lt": "4.17.21", "severity": "high", "note": "prototype pollution / ReDoS"},
    "minimist": {"lt": "1.2.6", "severity": "high", "note": "prototype pollution"},
    "node-fetch": {"lt": "2.6.7", "severity": "high", "note": "exposure of sensitive info on redirect"},
    "axios": {"lt": "0.21.2", "severity": "high", "note": "SSRF / open redirect"},
    "ejs": {"lt": "3.1.7", "severity": "high", "note": "template injection / RCE"},
    "serialize-javascript": {"lt": "3.1.0", "severity": "high", "note": "XSS via crafted payload"},
    "marked": {"lt": "4.0.10", "severity": "medium", "note": "ReDoS"},
    "tar": {"lt": "6.1.2", "severity": "high", "note": "arbitrary file overwrite"},
}

PYPI_ADVISORIES = {
    "pyyaml": {"lt": "5.4", "severity": "high", "note": "arbitrary code execution via full_load"},
    "requests": {"lt": "2.20.0", "severity": "medium", "note": "credential leak on redirect"},
    "jinja2": {"lt": "2.11.3", "severity": "medium", "note": "sandbox escape / ReDoS"},
    "flask": {"lt": "2.2.5", "severity": "medium", "note": "cookie parsing / security fixes"},
    "django": {"lt": "3.2.0", "severity": "high", "note": "multiple security fixes — upgrade to an LTS"},
}


def _parse_version(v: str):
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", v)
    if not m:
        return None
    return [int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)]


def _less_than(a, b) -> bool:
    for i in range(3):
        x, y = a[i], b[i]
        if x != y:
            return x < y
    return False


def _check_advisory(name: str, declared: str, advisories: dict):
    adv = advisories.get(name.lower())
    if not adv:
        return None
    ver = _parse_version(declared)
    if not ver:
        return None
    if "eq" in adv:
        eq = _parse_version(adv["eq"])
        if eq and ver == eq:
            return (adv["severity"], adv["note"])
        return None
    lt = _parse_version(adv["lt"])
    if lt and _less_than(ver, lt):
        return (adv["severity"], f"{adv['note']}; upgrade to >= {adv['lt']}")
    return None


def _scan_dependency_manifest(name: str, text: str, rel_file: str) -> list:
    base = name.replace("\\", "/").split("/")[-1].lower()
    findings = []
    if base == "package.json":
        try:
            pkg = json.loads(text)
        except json.JSONDecodeError:
            return findings
        deps = {}
        deps.update(pkg.get("dependencies") or {})
        deps.update(pkg.get("devDependencies") or {})
        for dep, rng in deps.items():
            hit = _check_advisory(dep, str(rng), NPM_ADVISORIES)
            if hit:
                findings.append({
                    "type": "vulnerable_dependency",
                    "severity": hit[0],
                    "confidence": "medium",
                    "line": 1,
                    "file": rel_file,
                    "message": f"Known-vulnerable dependency: {dep}@{rng} — {hit[1]}",
                    "snippet": f'"{dep}": "{rng}"',
                    "fix": f"Upgrade {dep} to a patched release; run your package manager's audit.",
                    "cwe": "CWE-1104",
                })
        return findings
    if base in ("requirements.txt", "requirements.in"):
        for i, raw in enumerate(text.split("\n"), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r"^([A-Za-z0-9._-]+)\s*==\s*([0-9][0-9A-Za-z.+-]*)", line)
            if not m:
                continue
            hit = _check_advisory(m.group(1), m.group(2), PYPI_ADVISORIES)
            if hit:
                findings.append({
                    "type": "vulnerable_dependency",
                    "severity": hit[0],
                    "confidence": "medium",
                    "line": i,
                    "file": rel_file,
                    "message": f"Known-vulnerable dependency: {m.group(1)}=={m.group(2)} — {hit[1]}",
                    "snippet": line[:120],
                    "fix": f"Upgrade {m.group(1)} to a patched release; run pip-audit.",
                    "cwe": "CWE-1104",
                })
    return findings


# --- scoring / dedupe / grouping --------------------------------------------

def _security_score(findings: list) -> tuple:
    penalty = 0.0
    for f in findings:
        base = SEVERITY_PENALTY.get(f.get("severity"), 1)
        factor = CONFIDENCE_FACTOR.get(f.get("confidence", "medium"), 0.65)
        penalty += base * factor
    score = max(0, round(100 - penalty))
    return score, _grade(score)


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _dedupe(findings: list) -> list:
    best = {}
    for f in findings:
        key = (f.get("file"), f.get("line"))
        cur = best.get(key)
        if cur is None:
            best[key] = f
            continue
        f_sev = SEVERITY_ORDER.get(f.get("severity"), 9)
        c_sev = SEVERITY_ORDER.get(cur.get("severity"), 9)
        if f_sev < c_sev:
            best[key] = f
        elif f_sev == c_sev:
            if CONFIDENCE_ORDER.get(f.get("confidence", "medium"), 1) < CONFIDENCE_ORDER.get(
                cur.get("confidence", "medium"), 1
            ):
                best[key] = f
    return list(best.values())


def _group_by_type(findings: list) -> list:
    groups = {}
    for f in findings:
        t = f.get("type") or "unknown"
        g = groups.get(t)
        if g:
            g["count"] += 1
            if SEVERITY_ORDER.get(f.get("severity"), 9) < SEVERITY_ORDER.get(g["severity"], 9):
                g["severity"] = f.get("severity")
        else:
            groups[t] = {"type": t, "count": 1, "severity": f.get("severity")}
    return sorted(groups.values(), key=lambda g: -g["count"])


def _severity_counts(findings: list) -> dict:
    c = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = str(f.get("severity", "low")).lower()
        if sev in c:
            c[sev] += 1
    return c


def _build_report(findings: list, slice_n: int, scanned_files: int = 0, suppressed: int = 0) -> dict:
    deduped = _dedupe(findings)
    deduped.sort(key=lambda x: SEVERITY_ORDER.get(str(x.get("severity", "low")), 9))
    counts = _severity_counts(deduped)
    urgent = counts["critical"] + counts["high"]
    score, grade = _security_score(deduped)
    return {
        "total": len(deduped),
        "findings": deduped[:slice_n],
        "truncated": len(deduped) > slice_n,
        "summary": f"{len(deduped)} issues found — {urgent} urgent",
        "score": score,
        "grade": grade,
        "byType": _group_by_type(deduped),
        "scannedFiles": scanned_files,
        "suppressed": suppressed,
        **counts,
    }


# --- .reposcope-ignore -------------------------------------------------------

INLINE_SUPPRESS_RE = re.compile(r"reposcope[-:]?\s*ignore", re.IGNORECASE)


def _glob_to_regex(glob: str):
    dir_only = glob.endswith("/")
    g = glob[:-1] if dir_only else glob
    anchored = g.startswith("/")
    if anchored:
        g = g[1:]
    out = []
    i = 0
    while i < len(g):
        c = g[i]
        if c == "*":
            if i + 1 < len(g) and g[i + 1] == "*":
                out.append(".*")
                i += 1
                if i + 1 < len(g) and g[i + 1] == "/":
                    i += 1
            else:
                out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c in ".+^${}()|[]\\":
            out.append("\\" + c)
        else:
            out.append(c)
        i += 1
    prefix = "^" if anchored else "(^|.*/)"
    return re.compile(prefix + "".join(out) + "(/.*)?$")


def _load_ignore(root: Path):
    patterns = []
    f = root / ".reposcope-ignore"
    try:
        if f.is_file():
            for raw in f.read_text(encoding="utf-8", errors="ignore").split("\n"):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    patterns.append(_glob_to_regex(line))
                except re.error:
                    pass
    except OSError:
        pass
    return patterns


def _ignored(patterns, rel_posix: str) -> bool:
    return any(p.search(rel_posix) for p in patterns)


def _apply_inline_suppression(findings: list, lines_by_file: dict) -> tuple:
    kept = []
    suppressed = 0
    for f in findings:
        lines = lines_by_file.get(f.get("file"))
        if lines:
            idx = int(f.get("line", 1)) - 1
            here = lines[idx] if 0 <= idx < len(lines) else None
            above = lines[idx - 1] if idx > 0 and idx - 1 < len(lines) else None
            if (here and INLINE_SUPPRESS_RE.search(here)) or (above and INLINE_SUPPRESS_RE.search(above)):
                suppressed += 1
                continue
        kept.append(f)
    return kept, suppressed


# --- public entrypoints ------------------------------------------------------

def vuln_scan(input_data: dict) -> dict:
    code = input_data.get("code") or input_data.get("diff", "")
    if not code:
        return {"error": "No code provided"}

    findings = []
    lines = code.split("\n")
    for name, pattern in PATTERNS.items():
        rx = re.compile(pattern)
        for i, line in enumerate(lines, 1):
            if rx.search(line):
                findings.append({
                    "type": name,
                    "severity": SEVERITY[name],
                    "confidence": CONFIDENCE.get(name),
                    "cwe": CWE.get(name),
                    "line": i,
                    "snippet": line.strip()[:100],
                    "fix": FIXES[name],
                    "message": FIXES[name],
                    "file": "",
                })

    return _build_report(findings, 5, scanned_files=1)


def vuln_scan_workspace(workspace_path: str) -> dict:
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return {"error": "workspacePath is not a directory"}

    ignore_patterns = _load_ignore(root)
    findings: list = []
    lines_by_file: dict = {}
    scanned = 0
    ignored_by_file = 0

    workspace_compiled = [(rule, sev, re.compile(pat)) for rule, sev, pat in WORKSPACE_RULES]
    pattern_compiled = [(name, re.compile(pat)) for name, pat in PATTERNS.items()]

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for name in filenames:
            if scanned >= MAX_WALK_FILES:
                break
            fp = Path(dirpath) / name
            suffix = fp.suffix.lower()
            env_file = _is_env_file(name)
            manifest = name.lower() in MANIFEST_FILES
            if suffix not in VULN_SCAN_SUFFIXES and not env_file and not manifest:
                continue
            try:
                if fp.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            rel = str(fp.relative_to(root)).replace(os.sep, "/")
            if _ignored(ignore_patterns, rel):
                ignored_by_file += 1
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            scanned += 1
            lines = text.split("\n")
            before = len(findings)

            if env_file:
                findings.extend(_scan_env_file(lines, rel))
            elif suffix in VULN_SCAN_SUFFIXES:
                findings.extend(_scan_source_lines(lines, rel, workspace_compiled, pattern_compiled))
            if manifest:
                findings.extend(_scan_dependency_manifest(name, text, rel))

            if len(findings) > before:
                lines_by_file[rel] = lines

    findings, suppressed = _apply_inline_suppression(findings, lines_by_file)
    return _build_report(
        findings,
        WORKSPACE_FINDING_CAP,
        scanned_files=scanned,
        suppressed=suppressed + ignored_by_file,
    )


def _scan_source_lines(lines: list, rel: str, workspace_compiled: list, pattern_compiled: list) -> list:
    found = []
    for rule, sev, rx in workspace_compiled:
        for i, line in enumerate(lines, 1):
            if _is_commented(line):
                continue
            if rx.search(line):
                msg, ffix = WORKSPACE_RULE_TEXT.get(
                    rule, (f"Suspicious pattern ({rule})", "Review and remove or refactor this line.")
                )
                found.append({
                    "type": rule,
                    "severity": sev,
                    "confidence": CONFIDENCE.get(rule),
                    "cwe": CWE.get(rule),
                    "line": i,
                    "file": rel,
                    "message": msg,
                    "snippet": line.strip()[:120],
                    "fix": ffix,
                })

    for name, rx in pattern_compiled:
        for i, line in enumerate(lines, 1):
            if _is_commented(line):
                continue
            if name == "hardcoded_url" and _is_env_fallback_url(line):
                continue
            if rx.search(line):
                found.append({
                    "type": name,
                    "severity": SEVERITY[name],
                    "confidence": CONFIDENCE.get(name),
                    "cwe": CWE.get(name),
                    "line": i,
                    "file": rel,
                    "message": FIXES[name],
                    "snippet": line.strip()[:120],
                    "fix": FIXES[name],
                })

    for i, line in enumerate(lines, 1):
        if _is_commented(line):
            continue
        ext = _scan_line_extended(line, i, rel)
        if ext:
            found.extend(ext)

    return found


def _main() -> None:
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        pa = Path(raw)
        if pa.is_file():
            try:
                code = pa.read_text(encoding="utf-8", errors="replace")
            except OSError:
                print(json.dumps({"error": "Could not read file"}))
                return
            print(json.dumps(vuln_scan({"code": code, "filePath": str(pa.resolve())})))
            return
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
