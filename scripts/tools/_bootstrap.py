"""Helpers for making tool entrypoints runnable from multiple working dirs."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def ensure_project_root_on_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root


def load_payload_from_argv() -> dict:
    if len(sys.argv) < 2:
        return {}
    return json.loads(sys.argv[1])


def print_result(result: dict) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))
