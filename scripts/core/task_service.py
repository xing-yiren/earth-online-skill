"""Task service for Earth Online skill.

Responsibilities:
- create tasks from structured input
- query active tasks
- complete once/daily tasks
- persist completion logs
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime

from .config import TASKS_FILE, ensure_data_root


class TaskService:
    """Manage task state in tasks.json."""

    def __init__(self) -> None:
        ensure_data_root()
        self.data_file = TASKS_FILE

    def create_task(self, payload: dict) -> dict:
        """Create a task from structured input."""

        data = self._load_data()
        name = (payload.get("name") or "").strip()
        task_type = payload.get("type", "main")
        recurrence = payload.get("recurrence", "once")

        if not name:
            return {
                "success": False,
                "error": "invalid_task_name",
                "message": "Task name is required.",
            }

        if task_type not in {"main", "side"}:
            return {
                "success": False,
                "error": "invalid_task_type",
                "message": "Task type must be 'main' or 'side'.",
            }

        if recurrence not in {"once", "daily"}:
            return {
                "success": False,
                "error": "invalid_recurrence",
                "message": "Task recurrence must be 'once' or 'daily'.",
            }

        duplicate = self._find_duplicate_task(data["tasks"], name, recurrence)
        if duplicate:
            return {
                "success": False,
                "error": "duplicate_task",
                "message": "A similar active task already exists.",
                "task": duplicate,
            }

        data["task_counter"] += 1
        now_iso = self._now_iso(payload.get("now"))
        task = {
            "id": self._make_task_id(data["task_counter"]),
            "name": name,
            "type": task_type,
            "recurrence": recurrence,
            "status": "active",
            "points": int(payload.get("points", 0)),
            "deadline": payload.get("deadline"),
            "created_at": now_iso,
            "updated_at": now_iso,
            "completed_at": None,
            "last_completed_date": None,
            "source": payload.get("source", "agent"),
        }
        data["tasks"].append(task)
        self._save_data(data)

        return {
            "success": True,
            "task": deepcopy(task),
        }

    def complete_task(self, payload: dict) -> dict:
        """Complete a task by id or fuzzy query."""

        data = self._load_data()
        task_id = payload.get("task_id")
        task_query = (payload.get("task_query") or "").strip()
        today = payload.get("date") or self._today()
        now_iso = self._now_iso(payload.get("now"))

        completed_once_task = self._find_completed_once_task(
            data["tasks"], task_id=task_id, task_query=task_query
        )
        if completed_once_task:
            return {
                "success": False,
                "error": "task_already_completed",
                "message": "This once task is already completed.",
                "task": self._public_task_view(completed_once_task),
            }

        matches = self._match_tasks(
            data["tasks"], task_id=task_id, task_query=task_query
        )
        if not matches:
            return {
                "success": False,
                "error": "task_not_found",
                "message": "No matching active task found.",
            }

        if len(matches) > 1:
            return {
                "success": False,
                "error": "needs_confirmation",
                "candidates": [self._public_task_view(task) for task in matches],
            }

        task = matches[0]

        if task["recurrence"] == "once":
            if task["status"] == "completed":
                return {
                    "success": False,
                    "error": "task_already_completed",
                    "message": "This once task is already completed.",
                    "task": self._public_task_view(task),
                }

            task["status"] = "completed"
            task["completed_at"] = now_iso
            task["updated_at"] = now_iso
            task["last_completed_date"] = today

        elif task["recurrence"] == "daily":
            if task.get("last_completed_date") == today:
                return {
                    "success": False,
                    "error": "task_already_completed_today",
                    "message": "This daily task is already completed today.",
                    "task": self._public_task_view(task),
                }

            task["last_completed_date"] = today
            task["updated_at"] = now_iso
            task["completed_at"] = now_iso

        else:
            return {
                "success": False,
                "error": "unsupported_recurrence",
                "message": "Unsupported task recurrence.",
            }

        log_entry = {
            "task_id": task["id"],
            "task_name": task["name"],
            "type": task["type"],
            "points": task["points"],
            "completion_kind": task["recurrence"],
            "completed_at": now_iso,
            "completed_date": today,
        }
        data["completion_log"].append(log_entry)
        self._save_data(data)

        return {
            "success": True,
            "task": self._public_task_view(task),
            "completion_log": log_entry,
        }

    def list_active_tasks(self) -> list[dict]:
        """Return all active tasks."""

        data = self._load_data()
        tasks = [task for task in data["tasks"] if task.get("status") == "active"]
        return [self._public_task_view(task) for task in tasks]

    def _load_data(self) -> dict:
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {
            "version": "1.0",
            "task_counter": 0,
            "tasks": [],
            "completion_log": [],
        }

    def _save_data(self, data: dict) -> None:
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def _find_duplicate_task(
        self, tasks: list[dict], name: str, recurrence: str
    ) -> dict | None:
        normalized_name = self._normalize(name)
        for task in tasks:
            if task.get("recurrence") != recurrence:
                continue
            if recurrence == "once" and task.get("status") != "active":
                continue
            if self._normalize(task.get("name", "")) == normalized_name:
                return self._public_task_view(task)
        return None

    def _match_tasks(
        self, tasks: list[dict], task_id: str | None, task_query: str
    ) -> list[dict]:
        if task_id:
            for task in tasks:
                if task.get("id") == task_id and not self._is_completed_once(task):
                    return [task]
            return []

        if not task_query:
            return []

        normalized_query = self._normalize(task_query)
        candidates = []
        for task in tasks:
            name = self._normalize(task.get("name", ""))
            if self._is_completed_once(task):
                continue
            if normalized_query in name or name in normalized_query:
                candidates.append(task)
        return candidates

    def _find_completed_once_task(
        self, tasks: list[dict], task_id: str | None, task_query: str
    ) -> dict | None:
        if task_id:
            for task in tasks:
                if task.get("id") == task_id and self._is_completed_once(task):
                    return task
            return None

        if not task_query:
            return None

        normalized_query = self._normalize(task_query)
        for task in tasks:
            if not self._is_completed_once(task):
                continue
            name = self._normalize(task.get("name", ""))
            if normalized_query in name or name in normalized_query:
                return task
        return None

    def _is_completed_once(self, task: dict) -> bool:
        return task.get("recurrence") == "once" and task.get("status") == "completed"

    def _make_task_id(self, counter: int) -> str:
        return f"task_{counter:04d}"

    def _public_task_view(self, task: dict) -> dict:
        return {
            "id": task.get("id"),
            "name": task.get("name"),
            "type": task.get("type"),
            "recurrence": task.get("recurrence"),
            "status": task.get("status"),
            "points": task.get("points"),
            "deadline": task.get("deadline"),
            "last_completed_date": task.get("last_completed_date"),
        }

    def _normalize(self, value: str) -> str:
        return " ".join(value.strip().lower().split())

    def _today(self) -> str:
        return datetime.now().date().isoformat()

    def _now_iso(self, override: str | None = None) -> str:
        if override:
            return override
        return datetime.now().astimezone().isoformat(timespec="seconds")
