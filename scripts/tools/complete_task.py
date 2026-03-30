"""Structured tool entrypoint for complete_task.

This module will coordinate task completion, points updates, and achievement
checks.
"""

from __future__ import annotations

from scripts.core.achievement_service import AchievementService
from scripts.core.points_service import PointsService
from scripts.core.task_service import TaskService


def run(payload: dict) -> dict:
    """Complete a task and trigger points and achievements updates."""

    task_service = TaskService()
    points_service = PointsService()
    achievement_service = AchievementService()

    task_result = task_service.complete_task(payload)
    if not task_result.get("success"):
        return task_result

    task = task_result["task"]
    completion_log = task_result["completion_log"]

    points_result = points_service.add_points(
        amount=task["points"],
        reason=f"完成任务：{task['name']}",
        source="task_complete",
        source_id=task["id"],
    )
    if not points_result.get("success"):
        return {
            "success": False,
            "error": "points_update_failed",
            "message": "Task completed, but points update failed.",
            "task": task,
            "completion_log": completion_log,
            "details": points_result,
        }

    achievement_result = achievement_service.record_task_completion(
        {"date": completion_log["completed_date"]}
    )
    if not achievement_result.get("success"):
        return {
            "success": False,
            "error": "achievement_update_failed",
            "message": "Task completed and points updated, but achievement update failed.",
            "task": task,
            "completion_log": completion_log,
            "points": points_result,
            "details": achievement_result,
        }

    reward_transactions = []
    for achievement in achievement_result.get("unlocked", []):
        reward_result = points_service.add_points(
            amount=achievement["reward_points"],
            reason=f"解锁成就：{achievement['name']}",
            source="achievement_unlock",
            source_id=achievement["id"],
        )
        if reward_result.get("success"):
            reward_transactions.append(reward_result["transaction"])

    final_stats = points_service.get_stats()

    return {
        "success": True,
        "task": task,
        "completion_log": completion_log,
        "task_points_transaction": points_result["transaction"],
        "unlocked_achievements": achievement_result.get("unlocked", []),
        "achievement_reward_transactions": reward_transactions,
        "points_stats": final_stats,
    }
