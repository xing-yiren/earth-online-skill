"""Structured tool entrypoint for apply_onboarding_imports."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools._bootstrap import load_payload_from_argv, print_result

from scripts.core.onboarding_import_service import OnboardingImportService
from scripts.renderers import render_apply_onboarding_imports


def run(payload: dict) -> dict:
    result = OnboardingImportService().apply_candidates(payload)
    if payload.get("render", False):
        result["message"] = render_apply_onboarding_imports(result)
    return result


if __name__ == "__main__":
    print_result(run(load_payload_from_argv()))
