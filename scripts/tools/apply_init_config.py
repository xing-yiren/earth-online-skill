"""Structured tool entrypoint for apply_init_config."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools._bootstrap import load_payload_from_argv, print_result

from scripts.core.init_service import InitService
from scripts.renderers import render_apply_init_config


def run(payload: dict) -> dict:
    result = InitService().apply_init_config(payload)
    if payload.get("render", False):
        result["message"] = render_apply_init_config(result)
    return result


if __name__ == "__main__":
    print_result(run(load_payload_from_argv()))
