"""Reward service for Earth Online skill.

Responsibilities:
- list enabled rewards
- resolve reward by id or name query
- append redemption history
"""

from __future__ import annotations

import json
from datetime import datetime

from .config import REWARDS_FILE, ensure_data_root


class RewardService:
    """Manage rewards catalog and redemption history."""

    def __init__(self) -> None:
        ensure_data_root()
        self.data_file = REWARDS_FILE

    def list_rewards(self, enabled_only: bool = True) -> dict:
        data = self._load_data()
        rewards = data["rewards"]
        if enabled_only:
            rewards = [item for item in rewards if item.get("is_enabled", False)]
        return {
            "success": True,
            "rewards": [self._public_reward_view(item) for item in rewards],
        }

    def get_reward(
        self, reward_query: str | None = None, reward_id: str | None = None
    ) -> dict:
        data = self._load_data()
        matches = self._match_rewards(
            data["rewards"], reward_query=reward_query, reward_id=reward_id
        )
        if not matches:
            return {
                "success": False,
                "error": "reward_not_found",
                "message": "No matching reward found.",
            }
        if len(matches) > 1:
            return {
                "success": False,
                "error": "needs_confirmation",
                "candidates": [self._public_reward_view(item) for item in matches],
            }
        return {
            "success": True,
            "reward": self._public_reward_view(matches[0]),
        }

    def record_redemption(
        self, reward_id: str, points_after: int, redeemed_at: str | None = None
    ) -> dict:
        data = self._load_data()
        reward = next(
            (item for item in data["rewards"] if item.get("id") == reward_id), None
        )
        if not reward:
            return {
                "success": False,
                "error": "reward_not_found",
                "message": "No matching reward found.",
            }

        entry = {
            "reward_id": reward["id"],
            "reward_name": reward["name"],
            "cost": reward["cost"],
            "redeemed_at": redeemed_at
            or datetime.now().astimezone().isoformat(timespec="seconds"),
            "points_after": points_after,
        }
        data["redemption_history"].append(entry)
        self._save_data(data)
        return {
            "success": True,
            "reward": self._public_reward_view(reward),
            "redemption": entry,
        }

    def _load_data(self) -> dict:
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {
            "version": "1.0",
            "rewards": [],
            "redemption_history": [],
        }

    def _save_data(self, data: dict) -> None:
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def _match_rewards(
        self, rewards: list[dict], reward_query: str | None, reward_id: str | None
    ) -> list[dict]:
        enabled_rewards = [item for item in rewards if item.get("is_enabled", False)]

        if reward_id:
            return [item for item in enabled_rewards if item.get("id") == reward_id]

        if not reward_query:
            return []

        normalized_query = self._normalize(reward_query)
        matches = []
        for reward in enabled_rewards:
            name = self._normalize(reward.get("name", ""))
            if normalized_query in name or name in normalized_query:
                matches.append(reward)
        return matches

    def _public_reward_view(self, reward: dict) -> dict:
        return {
            "id": reward.get("id"),
            "name": reward.get("name"),
            "cost": reward.get("cost"),
            "category": reward.get("category"),
            "description": reward.get("description"),
        }

    def _normalize(self, value: str) -> str:
        return " ".join(value.strip().lower().split())
