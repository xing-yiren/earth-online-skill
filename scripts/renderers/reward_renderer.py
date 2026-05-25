"""Reward-related renderers - game-style reward shop."""

from __future__ import annotations

from ._format import join_lines


def render_reward_list(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="⚠ 奖励商店读取失败。")

    rewards = result.get("rewards") or []
    if not rewards:
        return "▸ 奖励商店暂时空置，等积分攒起来了再来看看。"

    items = []
    for r in rewards:
        items.append(f"  • {r.get('name')}｜{r.get('cost', 0)} 积分｜{r.get('description', '')}")

    return join_lines([
        "▸ 当前可兑换奖励",
        "",
        "  ── 奖励商店 ──",
        *items,
        "",
        '想兑换哪个？说"我想兑换 XX"即可预览。',
    ])


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
            return join_lines([
                "▸ 积分不足",
                "",
                f"  {name} 需要 {cost} 积分",
                f"  当前积分：{current_points}",
                f"  还差：{abs(remaining)} 积分",
                "",
                "先完成一个主线或几个支线再回来兑换。",
            ])

        return join_lines([
            "▸ 奖励兑换预览",
            "",
            f"  奖励：{name}",
            f"  消耗：{cost} 积分",
            f"  兑换前积分：{current_points}",
            f"  兑换后剩余：{remaining} 积分",
            "",
            '确认兑换吗？回复"确认兑换"。',
        ])

    if error == "insufficient_points":
        reward = result.get("reward", {}) or {}
        required = result.get("required", reward.get("cost", 0))
        current = result.get("current_points", 0)
        name = reward.get("name")
        return join_lines([
            "▸ 积分不足",
            "",
            f"  {name or '该奖励'} 需要 {required} 积分",
            f"  当前积分：{current}",
            f"  还差：{max(required - current, 0)} 积分",
            "",
            "先完成一个主线或几个支线再回来兑换。",
        ])

    if error == "needs_confirmation":
        candidates = result.get("candidates") or []
        lines = ["▸ 匹配到多个奖励，请确认：", ""]
        for i, reward in enumerate(candidates, 1):
            lines.append(f"  {i}. {reward.get('name')}｜{reward.get('cost', 0)} 积分")
        return join_lines(lines)

    return _render_failure(result, default="⚠ 奖励兑换暂时无法继续。")


def render_reward_redeemed(result: dict) -> str:
    if not result.get("success"):
        return render_reward_preview(result)

    reward = result.get("reward", {}) or {}
    redemption = result.get("redemption", {}) or {}
    stats = result.get("points_stats", {}) or {}
    cost = redemption.get("cost", reward.get("cost", 0))
    points_after = redemption.get("points_after", stats.get("available_points", 0))

    return join_lines([
        "▸ 兑换成功 ✓",
        "",
        f"  奖励：{reward.get('name', '未命名奖励')}",
        f"  消耗积分：{cost}",
        f"  剩余积分：{points_after}",
        "",
        "已记录进兑换历史。记得真的去享受它！",
    ])


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
