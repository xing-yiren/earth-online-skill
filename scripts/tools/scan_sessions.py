"""Cross-session task scanner tool entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.core.session_scanner import SessionScanner
from scripts.renderers.onboarding_import_renderer import render_suggest_onboarding_imports
from scripts.tools._bootstrap import load_payload_from_argv, print_result


def run(payload: dict) -> dict:
    scanner = SessionScanner()
    result = scanner.scan(payload)

    if payload.get("render", False):
        result["message"] = render_suggest_onboarding_imports(result)

    return result


if __name__ == "__main__":
    payload = load_payload_from_argv()
    result = run(payload)
    print_result(result)
