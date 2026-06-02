import copy
import json
import re

GOALS_TEMPLATE = [
    {
        "id": "plugin-manifest",
        "task": "Finalize plugin.json manifest",
        "status": "done",
        "progress": 100,
        "keywords": ["manifest", "plugin.json", "hooks"],
    },
    {
        "id": "token-skill",
        "task": "Build token_audit skill",
        "status": "done",
        "progress": 100,
        "keywords": ["token", "ast", "unused import"],
    },
    {
        "id": "vuln-skill",
        "task": "Build vuln_scan skill",
        "status": "done",
        "progress": 100,
        "keywords": ["vuln", "security", "scan"],
    },
    {
        "id": "repo-skill",
        "task": "Build repo_trace skill",
        "status": "done",
        "progress": 100,
        "keywords": ["repo", "git", "trace"],
    },
    {
        "id": "gameplan-skill",
        "task": "Build game_plan skill",
        "status": "in-progress",
        "progress": 60,
        "keywords": ["game plan", "goals", "suggest"],
    },
    {
        "id": "crew-tests",
        "task": "CrewAI test suite passes",
        "status": "todo",
        "progress": 0,
        "keywords": ["test", "crew", "validation", "pass"],
    },
    {
        "id": "frontend-sidebar",
        "task": "Build sidebar UI (React/Webview)",
        "status": "todo",
        "progress": 0,
        "keywords": ["sidebar", "ui", "react", "webview", "frontend"],
    },
    {
        "id": "cursor-local-test",
        "task": "Test locally with cursor dev",
        "status": "todo",
        "progress": 0,
        "keywords": ["cursor dev", "local test", "extension host"],
    },
    {
        "id": "marketplace-submit",
        "task": "Submit to Cursor marketplace",
        "status": "todo",
        "progress": 0,
        "keywords": ["submit", "publish", "marketplace", "extension store"],
    },
    {
        "id": "token-licensing",
        "task": "Implement token-based licensing",
        "status": "todo",
        "progress": 0,
        "keywords": ["license", "token sale", "billing", "pro tier"],
    },
]


def update_game_plan(_repo_root: str = ".", agent_output: str | None = None) -> dict:
    goals = copy.deepcopy(GOALS_TEMPLATE)
    if agent_output:
        lower_out = agent_output.lower()
        for goal in goals:
            if any(kw in lower_out for kw in goal.get("keywords", [])):
                if re.search(r"(done|finished|added|implemented|merged|complete|built|created)", lower_out):
                    goal["status"] = "done"
                    goal["progress"] = 100

    total = len(goals)
    done = sum(1 for g in goals if g["status"] == "done")
    in_progress = sum(1 for g in goals if g["status"] == "in-progress")
    progress = int((done / total) * 100) if total else 0
    next_goal = next((g for g in goals if g["status"] == "todo"), None)

    return {
        "goals": goals,
        "progress": progress,
        "done": done,
        "in_progress": in_progress,
        "total": total,
        "next_step": next_goal["task"] if next_goal else "All tasks complete!",
        "summary": (
            f"{progress}% complete • {done}/{total} done • "
            f"Next: {next_goal['task'] if next_goal else 'Done!'}"
        ),
    }


def _main() -> None:
    import sys

    from entitlement import require_pro

    ok, gate = require_pro("Game Plan")
    if not ok:
        print(json.dumps(gate))
        return

    def emit(data: dict) -> None:
        out = data.get("output") or data.get("agentOutput")
        agent_output = out if isinstance(out, str) else None
        root = data.get("workspacePath") or data.get("workspaceRoot") or "."
        print(json.dumps(update_game_plan(str(root), agent_output)))

    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            if isinstance(data, dict):
                emit(data)
            else:
                print(json.dumps({"error": "argv JSON must be an object"}))
        except Exception:
            print(json.dumps(update_game_plan(".", None)))
        return

    raw_in = sys.stdin.read()
    if not raw_in.strip():
        print(json.dumps(update_game_plan(".", None)))
        return
    try:
        data = json.loads(raw_in)
    except json.JSONDecodeError:
        print(json.dumps({"error": "invalid stdin JSON"}))
        return
    if not isinstance(data, dict):
        print(json.dumps({"error": "stdin JSON must be an object"}))
        return
    emit(data)


if __name__ == "__main__":
    _main()
