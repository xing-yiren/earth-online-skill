"""Reward-related renderers - game-style reward shop."""

from __future__ import annotations

from ._format import join_lines


def render_reward_list(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="⚠ 奖励商店读取失败。")

    rewards = result.get("rewards") or []
    if not rewards:
        return "[奖励商店] 暂无商品"

    items = " | ".join(f"{r.get('name')}({r.get('cost', 0)}积分)" for r in rewards)
    return f"[奖励商店] {items}"


def render_reward_preview(result: dict) -> str:
    if result.get("success"):
        return render_reward_redeemed(result)

    error = result.get("error")
    if error == "confirmation_required":
        reward = result.get("reward", {}) or {}
        current_points = result.get("current_points", 0)
        cost = reward.get("cost", 0)
        remaining = current_points - cost
        name = reward.get('name', '未命名奖励')
        if remaining < 0:
            return f"[兑换预览] {name} | 需{cost}积分 | 当前{current_points}积分 | 不足{abs(remaining)}积分"
        return f"[兑换预览] {name} | 消耗{cost}积分 | 兑换前{current_points} | 兑换后{remaining} | 确认?"  # data card, needs user confirmation

    if error == "insufficient_points":
        reward = result.get("reward", {}) or {}
        required = result.get("required", reward.get("cost", 0))
        current = result.get("current_points", 0)
        name = reward.get("name")
        return f"[兑换失败] {name or '该奖励'} | 需{required}积分 | 当前{current} | 差{max(required - current, 0)}积分"

    if error == "needs_confirmation":
        candidates = result.get("candidates") or []
        items = " | ".join(f"{i}.{r.get('name')}({r.get('cost', 0)}积分)" for i, r in enumerate(candidates, 1))
        return f"[多候选] {items}"

    return _render_failure(result, default="⚠ 奖励兑换暂时无法继续。")


def render_reward_redeemed(result: dict) -> str:
    if not result.get("success"):
        return render_reward_preview(result)

    reward = result.get("reward", {}) or {}
    redemption = result.get("redemption", {}) or {}
    stats = result.get("points_stats", {}) or {}
    cost = redemption.get("cost", reward.get("cost", 0))
    points_after = redemption.get("points_after", stats.get("available_points", 0))

    return f"[兑换成功] {reward.get('name', '未命名奖励')} | 消耗{cost}积分 | 剩余{points_after}积分"


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
