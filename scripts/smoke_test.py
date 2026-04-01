"""Minimal integration smoke test for Earth Online skill.

This script runs the current V1 core flow against temporary copies of local
data files so it does not mutate project data.
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

from scripts.tools.complete_task import run as complete_task
from scripts.tools.create_task import run as create_task
from scripts.tools.get_daily_settlement import run as get_daily_settlement
from scripts.tools.get_morning_brief import run as get_morning_brief
from scripts.tools.list_rewards import run as list_rewards
from scripts.tools.record_morning_checkin import run as record_morning_checkin
from scripts.tools.redeem_reward import run as redeem_reward


def main() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    files = _copy_data_files(tmpdir)
    _patch_modules(files)

    results = {
        "morning_checkin": record_morning_checkin(
            {
                "current_time": "2026-03-25T07:20:00+08:00",
                "date": "2026-03-25",
            }
        ),
        "create_task": create_task(
            {
                "name": "整理周会纪要",
                "type": "main",
                "deadline": "2026-03-26",
                "source": "smoke_test",
                "now": "2026-03-25T09:00:00+08:00",
            }
        ),
        "morning_brief": get_morning_brief(
            {
                "date": "2026-03-25",
                "host_context": {
                    "user": {"name": "DemoUser", "timezone": "Asia/Shanghai"}
                },
            }
        ),
        "list_rewards": list_rewards({"enabled_only": True}),
        "redeem_preview": redeem_reward({"reward_query": "看电影", "confirm": False}),
    }

    created_task_name = (
        results["create_task"].get("task", {}).get("name", "整理周会纪要")
    )
    results["complete_task"] = complete_task(
        {
            "task_query": created_task_name,
            "date": "2026-03-25",
            "now": "2026-03-25T14:00:00+08:00",
        }
    )
    results["daily_settlement"] = get_daily_settlement({"date": "2026-03-25"})
    results["redeem_confirm"] = redeem_reward(
        {
            "reward_query": "看电影",
            "confirm": True,
            "redeemed_at": "2026-03-25T22:00:00+08:00",
        }
    )

    final_snapshot = {
        "tasks": json.loads(files["tasks"].read_text(encoding="utf-8")),
        "points": json.loads(files["points"].read_text(encoding="utf-8")),
        "achievements": json.loads(files["achievements"].read_text(encoding="utf-8")),
        "rewards": json.loads(files["rewards"].read_text(encoding="utf-8")),
    }

    print(
        json.dumps(
            {
                "results": results,
                "summary": {
                    "task_count": len(final_snapshot["tasks"]["tasks"]),
                    "completion_log_count": len(
                        final_snapshot["tasks"]["completion_log"]
                    ),
                    "points_history_count": len(final_snapshot["points"]["history"]),
                    "unlocked_count": len(final_snapshot["achievements"]["unlocked"]),
                    "redemption_history_count": len(
                        final_snapshot["rewards"]["redemption_history"]
                    ),
                    "available_points": final_snapshot["points"]["available_points"],
                    "current_level": final_snapshot["points"]["current_level"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


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
