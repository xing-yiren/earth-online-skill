"""Structured tool entrypoint for apply_init_config."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools._bootstrap import load_payload_from_argv, print_result

from scripts.core.init_service import InitService


def run(payload: dict) -> dict:
    return InitService().apply_init_config(payload)


if __name__ == "__main__":
    print_result(run(load_payload_from_argv()))
