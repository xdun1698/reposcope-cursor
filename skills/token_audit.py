import ast
import json
import os
import sys
from pathlib import Path

from shared import TOKEN_METRICS_SUFFIXES, estimate_tokens, iter_text_files, skip_token_metrics_path

MAX_AST_PY_FILES = 400


def _pick_breakdown_leader(prev: dict | None, rel: str, count: int) -> dict | None:
    """File with max count per category; tie-break: lexicographically smallest path."""
    if count <= 0:
        return prev
    if prev is None or count > prev["count"]:
        return {"path": rel, "count": count}
    if count == prev["count"] and rel < prev["path"]:
        return {"path": rel, "count": count}
    return prev


def _collect_import_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                names.add(alias.asname or base)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                names.add(alias.asname or alias.name)
    return names


def _collect_used_names(tree: ast.AST) -> set[str]:
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if isinstance(node.value, ast.Name):
                used.add(node.value.id)
    return used


def _collect_defs_and_calls(tree: ast.AST) -> tuple[set[str], set[str]]:
    defs: set[str] = set()
    calls: set[str] = set()
    method_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_names.add(item.name)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name not in method_names:
                defs.add(node.name)
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                calls.add(fn.id)
            elif isinstance(fn, ast.Attribute):
                calls.add(fn.attr)
    return defs, calls


def token_audit(file_path: str) -> dict:
    try:
        code = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(code)

        imported = _collect_import_names(tree)
        used_names = _collect_used_names(tree)
        unused_imports = len(imported - used_names)

        defs, calls = _collect_defs_and_calls(tree)
        dead_code = len(defs - calls)

        big_strings = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and len(node.value) > 200
        )

        total_tokens_saved = (unused_imports * 10) + (dead_code * 5) + (big_strings * 15)

        return {
            "unused_imports": unused_imports,
            "dead_code": dead_code,
            "big_strings": big_strings,
            "total_tokens_saved": total_tokens_saved,
        }
    except Exception as e:
        return {"error": str(e)}


def token_audit_workspace(workspace_path: str) -> dict:
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return {"error": "workspacePath is not a directory"}

    per_file: list[dict] = []
    for fp in iter_text_files(root, suffixes=TOKEN_METRICS_SUFFIXES):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(fp.relative_to(root)).replace(os.sep, "/")
        if skip_token_metrics_path(rel):
            continue
        tok = estimate_tokens(text)
        per_file.append({"path": rel, "tokens": tok})

    per_file.sort(key=lambda x: x["tokens"], reverse=True)
    total_tokens = sum(x["tokens"] for x in per_file)

    top5 = per_file[:5]
    hotspots = [
        {"path": x["path"], "type": "large_file", "tokens": x["tokens"]}
        for x in top5
    ]
    ranked_paths = [x["path"] for x in per_file[:50]]

    unused = dead = bigs = 0
    py_seen = 0
    leader_unused: dict | None = None
    leader_dead: dict | None = None
    leader_big: dict | None = None
    for fp in iter_text_files(root, suffixes=TOKEN_METRICS_SUFFIXES):
        if fp.suffix.lower() != ".py":
            continue
        if py_seen >= MAX_AST_PY_FILES:
            break
        py_seen += 1
        rel = str(fp.relative_to(root)).replace(os.sep, "/")
        r = token_audit(str(fp))
        if "error" in r:
            continue
        u = int(r.get("unused_imports", 0))
        d = int(r.get("dead_code", 0))
        b = int(r.get("big_strings", 0))
        unused += u
        dead += d
        bigs += b
        leader_unused = _pick_breakdown_leader(leader_unused, rel, u)
        leader_dead = _pick_breakdown_leader(leader_dead, rel, d)
        leader_big = _pick_breakdown_leader(leader_big, rel, b)

    top_files = [{"file": x["path"], "path": x["path"], "tokens": x["tokens"]} for x in top5]

    breakdown_leaders = {
        "unused_imports": leader_unused,
        "dead_code": leader_dead,
        "big_strings": leader_big,
    }

    return {
        "totalTokens": total_tokens,
        "total_tokens": total_tokens,
        "perFile": per_file[:200],
        "hotspots": hotspots,
        "hotspot_count": len(hotspots),
        "hotspotCount": len(hotspots),
        "rankedPaths": ranked_paths,
        "top_files": top_files,
        "unused_imports": unused,
        "dead_code": dead,
        "big_strings": bigs,
        "breakdown_leaders": breakdown_leaders,
        "breakdownLeaders": breakdown_leaders,
    }


def _main() -> None:
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        pa = Path(arg1)
        if pa.is_file():
            print(json.dumps(token_audit(arg1)))
            return
        if pa.is_dir():
            print(json.dumps(token_audit_workspace(str(pa.resolve()))))
            return
        try:
            data = json.loads(arg1)
        except json.JSONDecodeError:
            try:
                data = json.loads(Path(arg1).read_text(encoding="utf-8"))
            except Exception:
                print(json.dumps(token_audit(arg1)))
                return
        if not isinstance(data, dict):
            print(json.dumps({"error": "argv JSON must be an object"}))
            return
        ws = data.get("workspacePath") or data.get("workspaceRoot")
        if isinstance(ws, str) and ws:
            print(json.dumps(token_audit_workspace(ws)))
            return
        print(json.dumps({"error": "workspacePath or workspaceRoot required in argv JSON"}))
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

    print(json.dumps(token_audit_workspace(ws)))


if __name__ == "__main__":
    _main()
