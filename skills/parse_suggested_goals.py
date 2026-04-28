import json
import re


def parse_suggested_goals(agent_output: str, current_goals: list | None = None) -> dict:
    if not agent_output:
        return {"error": "No output", "summary": "No suggestions added"}

    pattern = (
        r"\d+\.\s*\[Priority:\s*(\w+)\]\s*Task:\s*(.+?)\s*Description:\s*(.+?)"
        r"(?=\d+\.\s*\[|Suggested additions complete|$)"
    )
    matches = re.findall(pattern, agent_output, re.DOTALL | re.IGNORECASE)

    new_goals = []
    for i, (prio, title, desc) in enumerate(matches):
        new_goals.append(
            {
                "id": f"suggested-{i + 1}",
                "task": title.strip(),
                "description": desc.strip(),
                "priority": prio.capitalize(),
                "status": "todo",
                "progress": 0,
                "keywords": title.lower().split()[:3],
            }
        )

    if current_goals:
        existing = {g["task"].lower().strip() for g in current_goals}
        new_goals = [g for g in new_goals if g["task"].lower().strip() not in existing]

    updated = (current_goals or []) + new_goals
    return {
        "goals": updated,
        "added": len(new_goals),
        "next_step": new_goals[0]["task"] if new_goals else "Review existing plan",
        "summary": f"Added {len(new_goals)} new goals • Total: {len(updated)}",
    }


def _main() -> None:
    import sys

    def emit(data: dict) -> None:
        out = data.get("output", "")
        if not isinstance(out, str):
            out = ""
        current = data.get("currentGoals") or data.get("current_goals") or data.get("goals")
        if current is not None and not isinstance(current, list):
            current = None
        print(json.dumps(parse_suggested_goals(out, current)))

    if len(sys.argv) > 1:
        try:
            data = json.loads(sys.argv[1])
            if isinstance(data, dict):
                emit(data)
            else:
                print(json.dumps({"error": "argv JSON must be an object"}))
        except Exception:
            print(json.dumps({"error": "Parse failed"}))
        return

    raw_in = sys.stdin.read()
    if not raw_in.strip():
        print(json.dumps({"error": "No output", "summary": "No suggestions added"}))
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
