"""Structured tool entrypoint for list_rewards."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.tools._bootstrap import load_payload_from_argv, print_result

from scripts.core.reward_service import RewardService


def run(payload: dict) -> dict:
    enabled_only = payload.get("enabled_only", True)
    return RewardService().list_rewards(enabled_only=enabled_only)


if __name__ == "__main__":
    print_result(run(load_payload_from_argv()))
