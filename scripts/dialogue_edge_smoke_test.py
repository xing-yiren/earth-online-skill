"""Dialogue edge-case smoke tests for Earth Online skill.

These checks focus on situations Claude Code must handle carefully in real
conversation: ambiguity, duplicate actions, corrections, and reward confirmation.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED_DATA_ROOT = ROOT / "examples" / "seed-data"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.core.achievement_service as achievement_mod
import scripts.core.points_service as points_mod
import scripts.core.reward_service as reward_mod
import scripts.core.settlement_service as settlement_mod
import scripts.core.task_service as task_mod
import scripts.tools.record_morning_checkin as morning_checkin_mod

from scripts.tools.cancel_task import run as cancel_task
from scripts.tools.complete_task import run as complete_task
from scripts.tools.create_task import run as create_task
from scripts.tools.get_daily_settlement import run as get_daily_settlement
from scripts.tools.record_morning_checkin import run as record_morning_checkin
from scripts.tools.redeem_reward import run as redeem_reward


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    files = _copy_data_files(tmpdir)
    _patch_modules(files)

    results = {
        "duplicate_task": _check_duplicate_task(),
        "ambiguous_completion": _check_ambiguous_completion(),
        "repeat_completion": _check_repeat_completion(),
        "cancelled_task_settlement": _check_cancelled_task_settlement(),
        "insufficient_reward_message": _check_insufficient_reward_message(),
        "morning_checkin_idempotency": _check_morning_checkin_idempotency(),
    }

    print(json.dumps({"success": True, "checks": results}, ensure_ascii=False, indent=2))


def _check_duplicate_task() -> dict:
    first = create_task(
        {
            "name": "整理项目计划",
            "type": "main",
            "now": "2026-03-25T09:00:00+08:00",
            "render": True,
        }
    )
    second = create_task(
        {
            "name": "整理项目计划",
            "type": "main",
            "now": "2026-03-25T09:01:00+08:00",
            "render": True,
        }
    )
    _assert(first["success"], "first duplicate setup task should be created")
    _assert(second["error"] == "duplicate_task", "duplicate task should be rejected")
    _assert("message" in second, "duplicate task should include rendered message")
    return {"error": second["error"], "message": second["message"]}


def _check_ambiguous_completion() -> dict:
    create_task(
        {
            "name": "完善项目计划",
            "type": "main",
            "now": "2026-03-25T09:02:00+08:00",
            "render": True,
        }
    )
    result = complete_task(
        {
            "task_query": "项目计划",
            "date": "2026-03-25",
            "render": True,
        }
    )
    _assert(result["error"] == "needs_confirmation", "ambiguous completion should require confirmation")
    _assert(len(result.get("candidates", [])) >= 2, "ambiguous completion should return candidates")
    _assert("message" in result, "ambiguous completion should include rendered message")
    return {"error": result["error"], "candidate_count": len(result["candidates"])}


def _check_repeat_completion() -> dict:
    create_task(
        {
            "name": "提交日报",
            "type": "main",
            "now": "2026-03-25T10:00:00+08:00",
            "render": True,
        }
    )
    first = complete_task(
        {
            "task_query": "提交日报",
            "date": "2026-03-25",
            "render": True,
        }
    )
    second = complete_task(
        {
            "task_query": "提交日报",
            "date": "2026-03-25",
            "render": True,
        }
    )
    _assert(first["success"], "first completion should succeed")
    _assert(second["error"] == "task_already_completed", "repeat completion should be rejected")
    _assert("message" in second, "repeat completion should include rendered message")
    return {"error": second["error"], "message": second["message"]}


def _check_cancelled_task_settlement() -> dict:
    task = create_task(
        {
            "name": "临时支线",
            "type": "side",
            "now": "2026-03-25T11:00:00+08:00",
            "render": True,
        }
    )
    cancel = cancel_task(
        {
            "task_id": task["task"]["id"],
            "now": "2026-03-25T11:01:00+08:00",
            "render": True,
        }
    )
    settlement = get_daily_settlement({"date": "2026-03-25", "render": True})
    pending_names = [item.get("name") for item in settlement.get("pending_tasks", [])]
    _assert(cancel["success"], "task cancellation should succeed")
    _assert("临时支线" not in pending_names, "cancelled side task should not be pending")
    return {"cancelled": cancel["task"]["name"], "pending_tasks": pending_names}


def _check_insufficient_reward_message() -> dict:
    result = redeem_reward({"reward_query": "看电影", "render": True})
    _assert(result["error"] == "confirmation_required", "reward preview should require confirmation")
    _assert("还差" in result["message"], "insufficient reward preview should explain point gap")
    return {"error": result["error"], "message": result["message"]}


def _check_morning_checkin_idempotency() -> dict:
    first = record_morning_checkin(
        {
            "current_time": "2026-03-26T07:20:00+08:00",
            "date": "2026-03-26",
            "render": True,
        }
    )
    second = record_morning_checkin(
        {
            "current_time": "2026-03-26T07:25:00+08:00",
            "date": "2026-03-26",
            "render": True,
        }
    )
    _assert(first["success"], "first morning checkin should succeed")
    _assert(second["already_recorded"], "second same-day morning checkin should be idempotent")
    _assert("message" in second, "idempotent checkin should include rendered message")
    return {"already_recorded": second["already_recorded"], "message": second["message"]}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _copy_data_files(tmpdir: Path) -> dict[str, Path]:
    files = {}
    for name in [
        "tasks.json",
        "points.json",
        "achievements.json",
        "rewards.json",
        "USER.md",
    ]:
        src = SEED_DATA_ROOT / name
        dst = tmpdir / name
        shutil.copy2(src, dst)
        key = name.replace(".json", "").replace(".md", "").lower()
        files[key] = dst
    return files


def _patch_modules(files: dict[str, Path]) -> None:
    task_mod.TASKS_FILE = files["tasks"]
    points_mod.POINTS_FILE = files["points"]
    achievement_mod.ACHIEVEMENTS_FILE = files["achievements"]
    reward_mod.REWARDS_FILE = files["rewards"]
    settlement_mod.TASKS_FILE = files["tasks"]
    settlement_mod.POINTS_FILE = files["points"]
    settlement_mod.ACHIEVEMENTS_FILE = files["achievements"]
    settlement_mod.USER_FILE = files["user"]
    morning_checkin_mod.USER_FILE = files["user"]


if __name__ == "__main__":
    main()
