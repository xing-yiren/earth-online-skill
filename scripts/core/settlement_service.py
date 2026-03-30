"""Read-only aggregation service for briefs and settlements.

Responsibilities:
- build morning brief data
- build daily settlement data
- combine task, points, achievement, and host context inputs
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from .config import ACHIEVEMENTS_FILE, POINTS_FILE, TASKS_FILE, USER_FILE


class SettlementService:
    """Build morning brief and daily settlement payloads."""

    def get_morning_brief(self, payload: dict) -> dict:
        host_context = payload.get("host_context", {})
        date = payload.get("date") or self._today()
        user = self._load_user_profile(host_context)
        tasks = self._load_tasks()
        points = self._load_points()
        achievements = self._load_achievements()

        main_tasks = []
        side_tasks = []
        for task in tasks["tasks"]:
            if task.get("status") != "active":
                continue
            item = {
                "id": task.get("id"),
                "name": task.get("name"),
                "points": task.get("points"),
                "deadline": task.get("deadline"),
            }
            if task.get("type") == "main":
                main_tasks.append(item)
            elif task.get("type") == "side":
                item["completed_today"] = task.get("last_completed_date") == date
                side_tasks.append(item)

        stats = achievements["stats"]
        return {
            "success": True,
            "player_name": user["name"],
            "date": date,
            "survival_days": stats.get("survival_days", 0),
            "early_bird_streak": stats.get("early_bird_streak", 0),
            "main_tasks": main_tasks,
            "side_tasks": side_tasks,
            "current_points": points.get("available_points", 0),
            "current_level": points.get("current_level", 1),
            "level_title": points.get("level_title", "新手玩家"),
        }

    def get_daily_settlement(self, payload: dict) -> dict:
        date = payload.get("date") or self._today()
        tasks = self._load_tasks()
        points = self._load_points()
        achievements = self._load_achievements()

        completed_logs = [
            item
            for item in tasks["completion_log"]
            if item.get("completed_date") == date
        ]
        main_completed = sum(1 for item in completed_logs if item.get("type") == "main")
        side_completed = sum(1 for item in completed_logs if item.get("type") == "side")
        main_total = sum(1 for item in tasks["tasks"] if item.get("type") == "main")
        side_total = sum(1 for item in tasks["tasks"] if item.get("type") == "side")
        points_earned_today = sum(item.get("points", 0) for item in completed_logs)

        completed_tasks = [
            {
                "name": item.get("task_name"),
                "type": item.get("type"),
                "points": item.get("points", 0),
            }
            for item in completed_logs
        ]

        pending_tasks = []
        for task in tasks["tasks"]:
            if task.get("type") == "main" and task.get("status") == "active":
                pending_tasks.append({"name": task.get("name"), "type": "main"})
            elif task.get("type") == "side" and task.get("last_completed_date") != date:
                pending_tasks.append({"name": task.get("name"), "type": "side"})

        new_achievements = [
            {"id": item.get("id"), "name": item.get("name")}
            for item in achievements["unlocked"]
            if item.get("unlocked_at", "").startswith(date)
        ]

        next_threshold = self._next_level_threshold(points.get("current_level", 1))
        points_to_next_level = None
        if next_threshold is not None:
            points_to_next_level = max(
                next_threshold - points.get("available_points", 0), 0
            )

        return {
            "success": True,
            "date": date,
            "main_completed": main_completed,
            "main_total": main_total,
            "side_completed": side_completed,
            "side_total": side_total,
            "points_earned_today": points_earned_today,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "new_achievements": new_achievements,
            "current_points": points.get("available_points", 0),
            "current_level": points.get("current_level", 1),
            "level_title": points.get("level_title", "新手玩家"),
            "points_to_next_level": points_to_next_level,
        }

    def _load_user_profile(self, host_context: dict) -> dict:
        name = host_context.get("user", {}).get("name")
        timezone = host_context.get("user", {}).get("timezone")

        user_file_data = self._read_text_file(USER_FILE)
        return {
            "name": name or self._extract_user_field(user_file_data, "name") or "玩家",
            "timezone": timezone
            or self._extract_user_field(user_file_data, "timezone")
            or "Asia/Shanghai",
        }

    def _load_tasks(self) -> dict:
        return self._read_json_file(
            TASKS_FILE,
            {"version": "1.0", "task_counter": 0, "tasks": [], "completion_log": []},
        )

    def _load_points(self) -> dict:
        return self._read_json_file(
            POINTS_FILE,
            {
                "version": "1.0",
                "available_points": 0,
                "lifetime_points": 0,
                "spent_points": 0,
                "current_level": 1,
                "level_title": "新手玩家",
                "history": [],
            },
        )

    def _load_achievements(self) -> dict:
        return self._read_json_file(
            ACHIEVEMENTS_FILE,
            {
                "version": "1.0",
                "stats": {
                    "survival_days": 0,
                    "early_bird_streak": 0,
                    "best_early_bird_streak": 0,
                    "tasks_completed_total": 0,
                    "last_active_date": None,
                },
                "unlocked": [],
            },
        )

    def _read_json_file(self, path, default: dict) -> dict:
        if path.exists():
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        return default

    def _read_text_file(self, path) -> str:
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _extract_user_field(self, content: str, field: str) -> str | None:
        match = re.search(rf"- \*\*{field}\*\*:\s*(.+?)(?:\n|$)", content)
        if not match:
            return None
        return match.group(1).strip()

    def _next_level_threshold(self, current_level: int) -> int | None:
        mapping = {
            1: 500,
            2: 1000,
            3: 2000,
            4: 4000,
            5: 7000,
        }
        return mapping.get(current_level)

    def _today(self) -> str:
        return datetime.now().date().isoformat()
