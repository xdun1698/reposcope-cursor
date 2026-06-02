"""Shared constants and utilities for Reposcope skill scripts."""

import os
from pathlib import Path

SKIP_DIR_NAMES = frozenset({
    ".git",
    "node_modules",
    "dist",
    "out",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".turbo",
    "vendor",
    "Pods",
    ".next",
    "coverage",
    "fixtures",
    # Unity / vendored noise (not first-party product source)
    "Library",
    "Logs",
    "UserSettings",
    "Packages",
    "ANTLR",
})

TEXT_SUFFIXES = frozenset({
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".cs", ".java", ".go", ".rs",
    ".md", ".json", ".yaml", ".yml", ".html", ".css", ".scss", ".sql", ".sh", ".txt",
    ".vue", ".svelte", ".rb", ".php", ".kt", ".swift", ".toml", ".xml",
})

# Footprint metrics (token audit, repo map): exclude .xml — vendor/API-doc XML dominates totals
# and is rarely first-party source worth counting toward AI context size.
TOKEN_METRICS_SUFFIXES = frozenset(TEXT_SUFFIXES - {".xml"})

MAX_WALK_FILES = 8000
MAX_FILE_BYTES = 512_000


# Filenames that are machine-generated dependency snapshots, not first-party source for context sizing.
_TOKEN_METRICS_SKIP_FILENAMES = frozenset({
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "Poetry.lock",
})


def skip_token_metrics_path(rel_posix: str) -> bool:
    """True for paths that should not inflate token/repo footprint metrics."""
    p = rel_posix.replace("\\", "/")
    parts = p.split("/")
    base = parts[-1] if parts else ""

    if base in _TOKEN_METRICS_SKIP_FILENAMES:
        return True

    # Third-party Unity store / package C# (very large; not this product's code)
    if "Dreamteck" in parts or "TriLib" in parts:
        return True

    # TextMesh Pro sample content (huge; not first-party)
    for i, seg in enumerate(parts):
        if seg == "TextMesh Pro" and i + 1 < len(parts) and parts[i + 1] == "Examples & Extras":
            return True

    if not p.endswith("/Resources/merges.txt"):
        return False
    if len(parts) < 3 or parts[-1] != "merges.txt" or parts[-2] != "Resources":
        return False
    return "Assets" in parts


def estimate_tokens(content: str) -> int:
    """Estimate token count. Uses tiktoken (cl100k_base) when available,
    falls back to len//4 heuristic otherwise."""
    if _tiktoken_enc is not None:
        return max(1, len(_tiktoken_enc.encode(content, disallowed_special=())))
    return max(1, len(content) // 4)


try:
    import tiktoken as _tiktoken
    _tiktoken_enc = _tiktoken.get_encoding("cl100k_base")
except Exception:
    _tiktoken_enc = None


def iter_text_files(root: Path, *, max_files: int = MAX_WALK_FILES,
                    max_bytes: int = MAX_FILE_BYTES,
                    suffixes: frozenset[str] = TEXT_SUFFIXES):
    """Walk a directory tree yielding text files, skipping common non-source dirs."""
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for name in filenames:
            if count >= max_files:
                return
            p = Path(dirpath) / name
            if p.suffix.lower() not in suffixes:
                continue
            try:
                if p.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            count += 1
            yield p
