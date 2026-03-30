"""Achievement service for Earth Online skill.

Responsibilities:
- update achievement-related stats
- evaluate unlock conditions
- prevent duplicate unlocks
- emit achievement reward results
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from .config import ACHIEVEMENTS_FILE, ensure_data_root


class AchievementService:
    """Manage achievement state in achievements.json."""

    ACHIEVEMENT_DEFS = [
        {
            "id": "first_day",
            "name": "新手玩家",
            "icon": "first-day",
            "reward_points": 10,
            "reason": "累计生存达到1天",
            "kind": "survival_days",
            "threshold": 1,
        },
        {
            "id": "survivor_7",
            "name": "生存学徒",
            "icon": "survivor-7",
            "reward_points": 30,
            "reason": "累计生存达到7天",
            "kind": "survival_days",
            "threshold": 7,
        },
        {
            "id": "survivor_30",
            "name": "生存专家",
            "icon": "survivor-30",
            "reward_points": 100,
            "reason": "累计生存达到30天",
            "kind": "survival_days",
            "threshold": 30,
        },
        {
            "id": "early_bird_3",
            "name": "早起学徒",
            "icon": "early-bird-3",
            "reward_points": 30,
            "reason": "连续早起达到3天",
            "kind": "early_bird_streak",
            "threshold": 3,
        },
        {
            "id": "early_bird_7",
            "name": "早起战士",
            "icon": "early-bird-7",
            "reward_points": 50,
            "reason": "连续早起达到7天",
            "kind": "early_bird_streak",
            "threshold": 7,
        },
        {
            "id": "early_bird_30",
            "name": "早起大师",
            "icon": "early-bird-30",
            "reward_points": 200,
            "reason": "连续早起达到30天",
            "kind": "early_bird_streak",
            "threshold": 30,
        },
        {
            "id": "task_master_10",
            "name": "任务达人",
            "icon": "task-master-10",
            "reward_points": 50,
            "reason": "累计完成任务达到10个",
            "kind": "tasks_completed_total",
            "threshold": 10,
        },
        {
            "id": "task_master_50",
            "name": "任务大师",
            "icon": "task-master-50",
            "reward_points": 200,
            "reason": "累计完成任务达到50个",
            "kind": "tasks_completed_total",
            "threshold": 50,
        },
    ]

    def __init__(self) -> None:
        ensure_data_root()
        self.data_file = ACHIEVEMENTS_FILE

    def record_task_completion(self, payload: dict) -> dict:
        """Update task completion stats and check new achievements."""

        data = self._load_data()
        stats = data["stats"]

        stats["tasks_completed_total"] += 1
        if payload.get("date"):
            stats["last_active_date"] = payload["date"]

        self._save_data(data)
        unlocked = self.check_new_achievements()

        return {
            "success": True,
            "stats": stats,
            "unlocked": unlocked,
        }

    def record_morning_checkin(self, payload: dict) -> dict:
        """Record a morning check-in and update early bird streak if eligible."""

        data = self._load_data()
        stats = data["stats"]

        current_time = payload.get("current_time")
        current_date = payload.get("date")
        if not current_time:
            current_time = datetime.now().astimezone().isoformat(timespec="seconds")
        if not current_date:
            current_date = current_time[:10]

        morning_target_time = payload.get("morning_target_time", "07:00")
        grace_minutes = int(payload.get("early_bird_grace_minutes", 30))
        is_early = self._is_within_early_window(
            current_time=current_time,
            current_date=current_date,
            morning_target_time=morning_target_time,
            grace_minutes=grace_minutes,
        )

        stats["last_active_date"] = current_date
        unlocked = []

        if is_early:
            last_early = stats.get("last_early_bird_date")
            if last_early == current_date:
                return {
                    "success": True,
                    "is_early_bird": True,
                    "already_recorded": True,
                    "stats": stats,
                    "unlocked": [],
                }

            if last_early and self._days_between(last_early, current_date) == 1:
                stats["early_bird_streak"] += 1
            else:
                stats["early_bird_streak"] = 1

            stats["best_early_bird_streak"] = max(
                stats.get("best_early_bird_streak", 0),
                stats["early_bird_streak"],
            )
            stats["last_early_bird_date"] = current_date
            self._save_data(data)
            unlocked = self.check_new_achievements()
        else:
            self._save_data(data)

        return {
            "success": True,
            "is_early_bird": is_early,
            "already_recorded": False,
            "stats": stats,
            "unlocked": unlocked,
        }

    def check_new_achievements(self) -> list[dict]:
        """Evaluate unlock conditions and append new achievements."""

        data = self._load_data()
        unlocked_ids = {item["id"] for item in data["unlocked"]}
        stats = data["stats"]
        new_items = []

        for definition in self.ACHIEVEMENT_DEFS:
            if definition["id"] in unlocked_ids:
                continue

            current_value = stats.get(definition["kind"], 0)
            if current_value < definition["threshold"]:
                continue

            unlocked = {
                "id": definition["id"],
                "name": definition["name"],
                "icon": definition["icon"],
                "reward_points": definition["reward_points"],
                "reason": definition["reason"],
                "unlocked_at": datetime.now()
                .astimezone()
                .isoformat(timespec="seconds"),
            }
            data["unlocked"].append(unlocked)
            new_items.append(unlocked)

        if new_items:
            self._save_data(data)

        return new_items

    def get_stats(self) -> dict:
        """Return achievement stats and unlocked list."""

        data = self._load_data()
        return {
            "stats": data["stats"],
            "unlocked": data["unlocked"],
        }

    def _load_data(self) -> dict:
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {
            "version": "1.0",
            "stats": {
                "survival_days": 0,
                "early_bird_streak": 0,
                "best_early_bird_streak": 0,
                "last_early_bird_date": None,
                "tasks_completed_total": 0,
                "last_active_date": None,
            },
            "unlocked": [],
        }

    def _save_data(self, data: dict) -> None:
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def _is_within_early_window(
        self,
        current_time: str,
        current_date: str,
        morning_target_time: str,
        grace_minutes: int,
    ) -> bool:
        timestamp = datetime.fromisoformat(current_time)
        target_hour, target_minute = [
            int(part) for part in morning_target_time.split(":", 1)
        ]
        window_start = datetime.fromisoformat(
            f"{current_date}T00:00:00{timestamp.strftime('%z')[:3]}:{timestamp.strftime('%z')[3:]}"
        )
        target = window_start.replace(hour=target_hour, minute=target_minute)
        deadline = target + timedelta(minutes=grace_minutes)
        return timestamp <= deadline

    def _days_between(self, earlier: str, later: str) -> int:
        earlier_date = datetime.fromisoformat(f"{earlier}T00:00:00").date()
        later_date = datetime.fromisoformat(f"{later}T00:00:00").date()
        return (later_date - earlier_date).days
