"""Onboarding smoke test for Earth Online initialization tools."""

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
    init_state = data_root / ".earth_online_init.json"
    if init_state.exists():
        init_state.unlink()

    env = dict(os.environ)
    env["EARTH_ONLINE_DATA_ROOT"] = str(data_root)
    env["PYTHONIOENCODING"] = "utf-8"

    missing_context = {
        "host_context": {
            "host": {"platform": "claude-code"},
            "user": {"id": "demo-user"},
            "session": {"current_date": "2026-03-25"},
            "context": {"uncertainties": ["user_name_missing", "timezone_missing"]},
        },
        "render": True,
    }

    init_result = _run_tool("init_skill_profile.py", missing_context, env)
    confirmation_failure = _run_tool(
        "apply_init_config.py",
        {
            "name": "DemoUser",
            "timezone": "Asia/Shanghai",
            "required_fields": ["name", "timezone"],
            "confirmed_fields": ["name", "timezone"],
            "render": True,
        },
        env,
    )
    unresolved_failure = _run_tool(
        "apply_init_config.py",
        {
            "confirmed_by_user": True,
            "name": "DemoUser",
            "timezone": "Asia/Shanghai",
            "required_fields": ["name", "timezone"],
            "confirmed_fields": ["name"],
            "render": True,
        },
        env,
    )
    apply_success = _run_tool(
        "apply_init_config.py",
        {
            "confirmed_by_user": True,
            "confirmed_fields": ["name", "timezone", "morning_target_time", "early_bird_grace_minutes"],
            "required_fields": ["name", "timezone"],
            "user_id": "demo-user",
            "name": "DemoUser",
            "timezone": "Asia/Shanghai",
            "morning_target_time": "07:00",
            "early_bird_grace_minutes": 30,
            "render": True,
        },
        env,
    )
    initialized_result = _run_tool("init_skill_profile.py", {"render": True}, env)
    suggested_imports = _run_tool(
        "suggest_onboarding_imports.py",
        {
            "raw_candidates": [
                {"name": "每日复盘三件事", "type": "side", "points": 20, "source": "memory"},
                {"name": "完成项目初始化验证", "type": "main", "points": 80, "source": "conversation"},
                "整理长期目标清单",
            ],
            "render": True,
        },
        env,
    )
    tasks_state_after_suggest = json.loads((data_root / "tasks.json").read_text(encoding="utf-8"))
    _assert(tasks_state_after_suggest["task_counter"] == 0, "suggestion stage must not write tasks")
    _assert(tasks_state_after_suggest["tasks"] == [], "suggestion stage must not create tasks")

    apply_imports = _run_tool(
        "apply_onboarding_imports.py",
        {
            "selected_candidates": suggested_imports["candidates"][:2],
            "now": "2026-03-25T09:30:00+08:00",
            "render": True,
        },
        env,
    )

    _assert(init_result["next_action"] == "ask_required_fields", "missing profile should ask required fields")
    _assert("message" in init_result, "init result should include message")
    _assert(confirmation_failure["error"] == "confirmation_required", "unconfirmed apply should fail")
    _assert("message" in confirmation_failure, "confirmation failure should include message")
    _assert(unresolved_failure["error"] == "required_fields_unresolved", "unresolved fields should fail")
    _assert("message" in unresolved_failure, "unresolved failure should include message")
    _assert(apply_success["success"], "confirmed apply should succeed")
    _assert("message" in apply_success, "successful apply should include message")
    _assert(initialized_result["initialized"], "profile should be initialized after apply")
    _assert("message" in initialized_result, "initialized check should include message")
    _assert(suggested_imports["success"], "candidate suggestion should succeed")
    _assert(suggested_imports["count"] == 3, "should normalize three candidates")
    _assert("message" in suggested_imports, "candidate suggestion should include message")

    _assert(apply_imports["success"], "candidate import should succeed")
    _assert(apply_imports["count"] == 2, "two confirmed candidates should be imported")
    _assert("message" in apply_imports, "candidate import should include message")
    tasks_state_after_apply = json.loads((data_root / "tasks.json").read_text(encoding="utf-8"))
    imported_names = {task["name"] for task in tasks_state_after_apply["tasks"]}
    _assert(imported_names == {"每日复盘三件事", "完成项目初始化验证"}, "imported task names should match selected candidates")

    print(
        json.dumps(
            {
                "success": True,
                "results": {
                    "init_result": init_result,
                    "confirmation_failure": confirmation_failure,
                    "unresolved_failure": unresolved_failure,
                    "apply_success": apply_success,
                    "initialized_result": initialized_result,
                    "suggested_imports": suggested_imports,
                    "apply_imports": apply_imports,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


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


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    main()
