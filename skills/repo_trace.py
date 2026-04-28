import json
import os
import subprocess
import sys
from pathlib import Path

from shared import TOKEN_METRICS_SUFFIXES, estimate_tokens, iter_text_files, skip_token_metrics_path


def _git_lines(root: Path, *git_args: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", *git_args],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return [ln for ln in out.split("\n") if ln.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return []


def repo_trace(repo_root: str) -> dict:
    root = Path(repo_root)
    if not root.is_dir():
        return {"error": "Not a directory", "summary": "Invalid repo root"}

    try:
        commits = _git_lines(root, "log", "--oneline", "-10")
        branches = _git_lines(root, "branch", "-a")
        changed_files = _git_lines(root, "diff", "--name-only", "HEAD~1", "HEAD")

        cursor_log: list = []
        log_path = Path.home() / ".cursor" / "logs" / "latest.json"
        if log_path.exists():
            try:
                payload = json.loads(log_path.read_text(encoding="utf-8"))
                cursor_log = payload.get("sessions", [])[-3:]
            except (OSError, json.JSONDecodeError):
                cursor_log = []

        return {
            "commits": commits,
            "branches": [b.strip() for b in branches],
            "changed": changed_files,
            "changedFiles": changed_files,
            "cursor_sessions": cursor_log,
            "summary": (
                f"{len(commits)} recent commits • {len(changed_files)} files touched • "
                f"{len(cursor_log)} Cursor runs"
            ),
        }
    except Exception as e:
        return {"error": str(e), "summary": "Git not found or repo not initialized"}


def repo_trace_workspace(workspace_path: str) -> dict:
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return {"error": "workspacePath is not a directory", "summary": "Invalid repo root"}

    files: list[dict] = []
    for fp in iter_text_files(root, suffixes=TOKEN_METRICS_SUFFIXES):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(fp.relative_to(root)).replace(os.sep, "/")
        if skip_token_metrics_path(rel):
            continue
        files.append({"path": rel, "tokens": estimate_tokens(text)})

    files.sort(key=lambda x: x["tokens"], reverse=True)

    branch_lines = _git_lines(root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_lines[0] if branch_lines else "unknown"

    short_commits = _git_lines(root, "log", "--oneline", "-5")
    branches = _git_lines(root, "branch", "-a")
    changed = _git_lines(root, "diff", "--name-only", "HEAD~1", "HEAD")

    cursor_log: list = []
    log_path = Path.home() / ".cursor" / "logs" / "latest.json"
    if log_path.exists():
        try:
            payload = json.loads(log_path.read_text(encoding="utf-8"))
            cursor_log = payload.get("sessions", [])[-3:]
        except (OSError, json.JSONDecodeError):
            cursor_log = []

    summary = (
        f"{len(files)} files scanned • branch {branch} • "
        f"{len(short_commits)} recent commits • {len(changed)} changed files"
    )

    return {
        "files": files[:500],
        "branch": branch,
        "commits": short_commits,
        "branches": [b.strip() for b in branches],
        "changed": changed,
        "changedFiles": changed,
        "cursor_sessions": cursor_log,
        "summary": summary,
    }


def _main() -> None:
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        pa = Path(arg1)
        if pa.is_dir():
            print(json.dumps(repo_trace_workspace(str(pa.resolve()))))
            return
        print(json.dumps(repo_trace(arg1)))
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

    ws = data.get("workspacePath") or data.get("workspaceRoot")
    if not ws or not isinstance(ws, str):
        print(json.dumps({"error": "workspacePath or workspaceRoot required"}))
        return

    print(json.dumps(repo_trace_workspace(ws)))


if __name__ == "__main__":
    _main()
