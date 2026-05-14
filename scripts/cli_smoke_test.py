"""CLI smoke test for Earth Online tool entrypoints.

This test runs tools as subprocesses with JSON argv payloads, matching the way
Claude Code can call the scripts directly during manual skill development.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED_DATA_ROOT = ROOT / "examples" / "seed-data"


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    data_root = tmpdir / "data"
    _copy_seed_data(data_root)

    env = dict(os.environ)
    env["EARTH_ONLINE_DATA_ROOT"] = str(data_root)
    env["PYTHONIOENCODING"] = "utf-8"

    results = {
        "morning_checkin": _run_tool(
            "record_morning_checkin.py",
            {
                "current_time": "2026-03-25T07:20:00+08:00",
                "date": "2026-03-25",
                "render": True,
            },
            env,
        ),
        "create_task": _run_tool(
            "create_task.py",
            {
                "name": "整理 CLI 验证记录",
                "type": "main",
                "now": "2026-03-25T09:00:00+08:00",
                "render": True,
            },
            env,
        ),
        "list_active_tasks": _run_tool("list_active_tasks.py", {"render": True}, env),
        "complete_task": _run_tool(
            "complete_task.py",
            {
                "task_query": "CLI 验证",
                "date": "2026-03-25",
                "now": "2026-03-25T14:00:00+08:00",
                "render": True,
            },
            env,
        ),
        "daily_settlement": _run_tool(
            "get_daily_settlement.py",
            {"date": "2026-03-25", "player_name": "DemoUser", "render": True},
            env,
        ),
        "list_rewards": _run_tool("list_rewards.py", {"render": True}, env),
        "redeem_preview": _run_tool(
            "redeem_reward.py",
            {"reward_query": "看电影", "render": True},
            env,
        ),
    }

    _assert_messages(results)
    print(json.dumps({"success": True, "results": results}, ensure_ascii=False, indent=2))


def _run_tool(tool_name: str, payload: dict, env: dict[str, str]) -> dict:
    command = [sys.executable, str(ROOT / "scripts" / "tools" / tool_name), json.dumps(payload, ensure_ascii=False)]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return json.loads(completed.stdout)


def _copy_seed_data(data_root: Path) -> None:
    data_root.mkdir(parents=True, exist_ok=True)
    for path in SEED_DATA_ROOT.iterdir():
        if path.is_file():
            shutil.copy2(path, data_root / path.name)


def _assert_messages(results: dict[str, dict]) -> None:
    missing = [name for name, result in results.items() if not result.get("message")]
    if missing:
        raise AssertionError(f"Missing CLI rendered messages: {', '.join(missing)}")


if __name__ == "__main__":
    main()
