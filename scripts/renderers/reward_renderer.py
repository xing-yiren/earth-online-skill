"""Reward-related renderers."""

from __future__ import annotations

from ._format import join_lines, section


def render_reward_list(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="奖励列表读取失败。")

    rewards = result.get("rewards") or []
    if not rewards:
        return "当前没有可兑换奖励。"

    items = [
        f"{reward.get('name')}｜{reward.get('cost', 0)} 积分｜{reward.get('description', '')}"
        for reward in rewards
    ]
    return join_lines(["当前可兑换奖励：", "", *section("奖励目录", items)])


def render_reward_preview(result: dict) -> str:
    if result.get("success"):
        return render_reward_redeemed(result)

    error = result.get("error")
    if error == "confirmation_required":
        reward = result.get("reward", {}) or {}
        current_points = result.get("current_points", 0)
        cost = reward.get("cost", 0)
        remaining = current_points - cost
        if remaining < 0:
            return join_lines(
                [
                    "当前积分还不够兑换这个奖励。",
                    f"【{reward.get('name', '未命名奖励')}】需要 {cost} 积分",
                    f"你当前有 {current_points} 积分",
                    f"还差：{abs(remaining)} 积分",
                    "",
                    "可以先完成一个主线任务，或者清几个支线任务再回来兑换。",
                ]
            )
        return join_lines(
            [
                "检测到你想兑换奖励：",
                "",
                f"【{reward.get('name', '未命名奖励')}】",
                f"消耗：{cost} 积分",
                f"当前积分：{current_points}",
                f"兑换后剩余：{remaining} 积分",
                "",
                "确认兑换吗？你可以回复“确认兑换”。",
            ]
        )
    if error == "insufficient_points":
        required = result.get("required", 0)
        current = result.get("current_points", 0)
        return join_lines(
            [
                "当前积分还不够兑换这个奖励。",
                f"需要积分：{required}",
                f"当前积分：{current}",
                f"还差：{max(required - current, 0)} 积分",
                "",
                "可以先完成一个主线任务，或者清几个支线任务再回来兑换。",
            ]
        )
    if error == "needs_confirmation":
        candidates = result.get("candidates") or []
        lines = ["匹配到多个奖励，请确认想兑换哪一个："]
        for index, reward in enumerate(candidates, 1):
            lines.append(f"{index}. {reward.get('name')}｜{reward.get('cost', 0)} 积分")
        return join_lines(lines)
    return _render_failure(result, default="奖励兑换暂时无法继续。")


def render_reward_redeemed(result: dict) -> str:
    if not result.get("success"):
        return render_reward_preview(result)

    reward = result.get("reward", {}) or {}
    redemption = result.get("redemption", {}) or {}
    stats = result.get("points_stats", {}) or {}
    cost = redemption.get("cost", reward.get("cost", 0))
    points_after = redemption.get("points_after", stats.get("available_points", 0))

    return join_lines(
        [
            "兑换成功。",
            "",
            f"奖励：【{reward.get('name', '未命名奖励')}】",
            f"消耗积分：{cost}",
            f"剩余积分：{points_after}",
            "",
            "本次奖励已经记录进兑换历史。记得真的去享受它，不要只是在系统里兑换。",
        ]
    )


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
