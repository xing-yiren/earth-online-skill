"""Points service for Earth Online skill.

Responsibilities:
- add and deduct points
- calculate levels
- maintain transaction history
"""

from __future__ import annotations

import json
from datetime import datetime

from .config import POINTS_FILE, ensure_data_root


class PointsService:
    """Manage points and level state in points.json."""

    LEVELS = [
        {"level": 1, "min_points": 0, "title": "新手玩家"},
        {"level": 2, "min_points": 500, "title": "资深玩家"},
        {"level": 3, "min_points": 1000, "title": "高级玩家"},
        {"level": 4, "min_points": 2000, "title": "精英玩家"},
        {"level": 5, "min_points": 4000, "title": "大师玩家"},
        {"level": 6, "min_points": 7000, "title": "传奇玩家"},
    ]

    def __init__(self) -> None:
        ensure_data_root()
        self.data_file = POINTS_FILE

    def add_points(self, amount: int, reason: str, source: str, source_id: str) -> dict:
        """Add points and append an earn transaction."""

        if amount <= 0:
            return {
                "success": False,
                "error": "invalid_amount",
                "message": "Amount must be greater than zero.",
            }

        data = self._load_data()
        data["available_points"] += amount
        data["lifetime_points"] += amount

        level_info = self._calculate_level(data["available_points"])
        data["current_level"] = level_info["level"]
        data["level_title"] = level_info["title"]

        transaction = self._make_transaction(
            data=data,
            txn_type="earn",
            amount=amount,
            reason=reason,
            source=source,
            source_id=source_id,
        )
        data["history"].append(transaction)
        self._save_data(data)

        return {
            "success": True,
            "transaction": transaction,
            "stats": self.get_stats(),
        }

    def deduct_points(
        self, amount: int, reason: str, source: str, source_id: str
    ) -> dict:
        """Deduct points and append a spend transaction."""

        if amount <= 0:
            return {
                "success": False,
                "error": "invalid_amount",
                "message": "Amount must be greater than zero.",
            }

        data = self._load_data()
        if data["available_points"] < amount:
            return {
                "success": False,
                "error": "insufficient_points",
                "required": amount,
                "current_points": data["available_points"],
            }

        data["available_points"] -= amount
        data["spent_points"] += amount

        level_info = self._calculate_level(data["available_points"])
        data["current_level"] = level_info["level"]
        data["level_title"] = level_info["title"]

        transaction = self._make_transaction(
            data=data,
            txn_type="spend",
            amount=amount,
            reason=reason,
            source=source,
            source_id=source_id,
        )
        data["history"].append(transaction)
        self._save_data(data)

        return {
            "success": True,
            "transaction": transaction,
            "stats": self.get_stats(),
        }

    def get_stats(self) -> dict:
        """Return current points and level summary."""

        data = self._load_data()
        next_level = self._get_next_level(data["current_level"])

        return {
            "available_points": data["available_points"],
            "lifetime_points": data["lifetime_points"],
            "spent_points": data["spent_points"],
            "current_level": data["current_level"],
            "level_title": data["level_title"],
            "points_to_next_level": None
            if not next_level
            else max(next_level["min_points"] - data["available_points"], 0),
        }

    def _load_data(self) -> dict:
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {
            "version": "1.0",
            "available_points": 0,
            "lifetime_points": 0,
            "spent_points": 0,
            "current_level": 1,
            "level_title": "新手玩家",
            "history": [],
        }

    def _save_data(self, data: dict) -> None:
        with open(self.data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def _calculate_level(self, available_points: int) -> dict:
        current = self.LEVELS[0]
        for level in self.LEVELS:
            if available_points >= level["min_points"]:
                current = level
        return current

    def _get_next_level(self, current_level: int) -> dict | None:
        for level in self.LEVELS:
            if level["level"] == current_level + 1:
                return level
        return None

    def _make_transaction(
        self,
        data: dict,
        txn_type: str,
        amount: int,
        reason: str,
        source: str,
        source_id: str,
    ) -> dict:
        txn_index = len(data["history"]) + 1
        return {
            "id": f"txn_{txn_index:04d}",
            "type": txn_type,
            "amount": amount,
            "source": source,
            "source_id": source_id,
            "reason": reason,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
