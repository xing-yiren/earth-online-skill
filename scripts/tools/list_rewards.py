"""Structured tool entrypoint for list_rewards."""

from scripts.core.reward_service import RewardService


def run(payload: dict) -> dict:
    enabled_only = payload.get("enabled_only", True)
    return RewardService().list_rewards(enabled_only=enabled_only)
