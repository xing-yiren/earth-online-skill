"""Structured tool entrypoint for redeem_reward."""

from __future__ import annotations

from scripts.core.points_service import PointsService
from scripts.core.reward_service import RewardService


def run(payload: dict) -> dict:
    reward_service = RewardService()
    points_service = PointsService()

    lookup = reward_service.get_reward(
        reward_query=payload.get("reward_query"),
        reward_id=payload.get("reward_id"),
    )
    if not lookup.get("success"):
        return lookup

    reward = lookup["reward"]
    if not payload.get("confirm", False):
        stats = points_service.get_stats()
        return {
            "success": False,
            "error": "confirmation_required",
            "reward": reward,
            "current_points": stats["available_points"],
        }

    deduct_result = points_service.deduct_points(
        amount=reward["cost"],
        reason=f"兑换奖励：{reward['name']}",
        source="reward_redeem",
        source_id=reward["id"],
    )
    if not deduct_result.get("success"):
        return deduct_result

    current_points = deduct_result["stats"]["available_points"]
    record_result = reward_service.record_redemption(
        reward_id=reward["id"],
        points_after=current_points,
        redeemed_at=payload.get("redeemed_at"),
    )
    if not record_result.get("success"):
        return {
            "success": False,
            "error": "reward_record_failed",
            "message": "Points deducted, but reward redemption record failed.",
            "reward": reward,
            "points": deduct_result,
            "details": record_result,
        }

    return {
        "success": True,
        "reward": reward,
        "points_transaction": deduct_result["transaction"],
        "redemption": record_result["redemption"],
        "points_stats": deduct_result["stats"],
    }
