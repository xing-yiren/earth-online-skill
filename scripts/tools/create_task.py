"""Structured tool entrypoint for create_task.

This module will accept structured input from the host runtime and delegate to
TaskService.
"""

from __future__ import annotations

from scripts.core.task_service import TaskService


DEFAULT_POINTS = {
    ("main", "once"): 80,
    ("main", "daily"): 50,
    ("side", "once"): 20,
    ("side", "daily"): 20,
}


def run(payload: dict) -> dict:
    """Create a task from structured input.

    Expected payload keys:
    - name
    - type: main | side
    - recurrence: once | daily
    - deadline: optional
    - points: optional
    - source: optional
    - host_context: optional, currently passthrough metadata
    """

    task_type = payload.get("type", "main")
    recurrence = payload.get("recurrence") or _default_recurrence(task_type)
    points = payload.get("points")
    if points is None:
        points = DEFAULT_POINTS.get((task_type, recurrence), 50)

    normalized_payload = {
        "name": payload.get("name"),
        "type": task_type,
        "recurrence": recurrence,
        "deadline": payload.get("deadline"),
        "points": points,
        "source": payload.get("source", "agent"),
        "now": payload.get("now"),
    }

    result = TaskService().create_task(normalized_payload)
    if not result.get("success"):
        return result

    return {
        "success": True,
        "task": result["task"],
    }


def _default_recurrence(task_type: str) -> str:
    if task_type == "side":
        return "daily"
    return "once"
