"""Structured tool entrypoint for list_active_tasks."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools._bootstrap import load_payload_from_argv, print_result

from scripts.core.task_service import TaskService
from scripts.renderers import render_active_tasks


def run(payload: dict) -> dict:
    tasks = TaskService().list_active_tasks()
    result = {
        "success": True,
        "tasks": tasks,
    }
    if payload.get("render", False):
        result["message"] = render_active_tasks(tasks)
    return result


if __name__ == "__main__":
    print_result(run(load_payload_from_argv()))
