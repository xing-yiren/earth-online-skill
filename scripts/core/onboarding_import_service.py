"""Optional onboarding import service for Earth Online skill.

This service generates candidate tasks from user-approved context snippets and
imports only the candidates the user explicitly confirms.
"""

from __future__ import annotations

from copy import deepcopy

from .task_service import TaskService


class OnboardingImportService:
    """Prepare onboarding task candidates and import confirmed selections."""

    def __init__(self) -> None:
        self.task_service = TaskService()

    def suggest_candidates(self, payload: dict) -> dict:
        raw_candidates = payload.get("raw_candidates") or []
        default_source = payload.get("default_source", "conversation")
        suggested = []

        for index, item in enumerate(raw_candidates, 1):
            candidate = self._normalize_candidate(
                item,
                candidate_id=f"candidate_{index:03d}",
                default_source=default_source,
            )
            if candidate:
                suggested.append(candidate)

        return {
            "success": True,
            "candidates": suggested,
            "count": len(suggested),
        }

    def apply_candidates(self, payload: dict) -> dict:
        selected_candidates = payload.get("selected_candidates") or []
        now = payload.get("now")
        source = payload.get("source", "onboarding_import")

        if not selected_candidates:
            return {
                "success": False,
                "error": "no_candidates_selected",
                "message": "No confirmed candidates were provided for import.",
            }

        imported = []
        skipped = []

        for item in selected_candidates:
            candidate = self._normalize_candidate(item)
            if not candidate:
                skipped.append(
                    {
                        "id": item.get("id") if isinstance(item, dict) else None,
                        "name": item.get("name") if isinstance(item, dict) else None,
                        "error": "invalid_candidate",
                    }
                )
                continue

            result = self.task_service.create_task(
                {
                    "name": candidate["name"],
                    "type": candidate["type"],
                    "recurrence": candidate["recurrence"],
                    "points": candidate["points"],
                    "deadline": candidate.get("deadline"),
                    "source": source,
                    "now": now,
                }
            )
            if result.get("success"):
                task = deepcopy(result["task"])
                task["source_candidate_id"] = candidate["id"]
                task["source_detail"] = candidate.get("source_detail")
                imported.append(task)
            else:
                skipped.append(
                    {
                        "id": candidate["id"],
                        "name": candidate["name"],
                        "error": result.get("error"),
                        "task": result.get("task"),
                    }
                )

        return {
            "success": True,
            "imported": imported,
            "skipped": skipped,
            "count": len(imported),
        }

    def _normalize_candidate(
        self,
        item,
        candidate_id: str | None = None,
        default_source: str = "conversation",
    ) -> dict | None:
        if isinstance(item, str):
            name = item.strip()
            if not name:
                return None
            return {
                "id": candidate_id or "candidate_manual",
                "name": name,
                "type": "main",
                "recurrence": "once",
                "points": 80,
                "source": default_source,
                "source_detail": "用户提供的候选文本",
                "raw_text": name,
            }

        if not isinstance(item, dict):
            return None

        name = (item.get("name") or item.get("raw_text") or "").strip()
        if not name:
            return None

        task_type = item.get("type") or "main"
        if task_type not in {"main", "side"}:
            task_type = "main"

        recurrence = item.get("recurrence")
        if recurrence not in {"once", "daily"}:
            recurrence = "daily" if task_type == "side" else "once"

        points = item.get("points")
        if points is None:
            points = 20 if task_type == "side" else 80

        return {
            "id": item.get("id") or candidate_id or "candidate_manual",
            "name": name,
            "type": task_type,
            "recurrence": recurrence,
            "points": int(points),
            "deadline": item.get("deadline"),
            "source": item.get("source") or default_source,
            "source_detail": item.get("source_detail") or "候选任务",
            "raw_text": item.get("raw_text") or name,
        }
