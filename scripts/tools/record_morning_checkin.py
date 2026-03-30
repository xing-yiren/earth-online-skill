"""Structured tool entrypoint for record_morning_checkin."""

from __future__ import annotations

import re

from scripts.core.achievement_service import AchievementService
from scripts.core.config import USER_FILE
from scripts.core.points_service import PointsService


def run(payload: dict) -> dict:
    settings = _load_morning_settings()
    normalized_payload = {
        "current_time": payload.get("current_time"),
        "date": payload.get("date"),
        "morning_target_time": payload.get(
            "morning_target_time", settings["morning_target_time"]
        ),
        "early_bird_grace_minutes": payload.get(
            "early_bird_grace_minutes", settings["early_bird_grace_minutes"]
        ),
    }

    achievement_result = AchievementService().record_morning_checkin(normalized_payload)
    if not achievement_result.get("success"):
        return achievement_result

    reward_transactions = []
    points_service = PointsService()
    for achievement in achievement_result.get("unlocked", []):
        reward_result = points_service.add_points(
            amount=achievement["reward_points"],
            reason=f"解锁成就：{achievement['name']}",
            source="achievement_unlock",
            source_id=achievement["id"],
        )
        if reward_result.get("success"):
            reward_transactions.append(reward_result["transaction"])

    result = dict(achievement_result)
    result["achievement_reward_transactions"] = reward_transactions
    result["points_stats"] = points_service.get_stats()
    return result


def _load_morning_settings() -> dict:
    content = USER_FILE.read_text(encoding="utf-8") if USER_FILE.exists() else ""
    target_time = _extract_field(content, "morning_target_time") or "07:00"
    grace_minutes = _extract_field(content, "early_bird_grace_minutes") or "30"
    return {
        "morning_target_time": target_time,
        "early_bird_grace_minutes": int(grace_minutes),
    }


def _extract_field(content: str, field: str) -> str | None:
    match = re.search(rf"- \*\*{field}\*\*:\s*(.+?)(?:\n|$)", content)
    if not match:
        return None
    return match.group(1).strip()
