"""Structured tool entrypoint for get_morning_brief."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools._bootstrap import load_payload_from_argv, print_result

from scripts.core.settlement_service import SettlementService


def run(payload: dict) -> dict:
    return SettlementService().get_morning_brief(payload)


if __name__ == "__main__":
    print_result(run(load_payload_from_argv()))
