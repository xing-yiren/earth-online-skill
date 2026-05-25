"""Daily settlement renderer — game-style dungeon settlement."""

from __future__ import annotations

from ._format import join_lines


_TYPE_LABEL = {"main": "主线", "side": "支线"}


def render_daily_settlement(result: dict, player_name: str | None = None) -> str:
    if not result.get("success"):
        return _render_failure(result, default="⚠ 副本结算失败，系统异常。")

    date = result.get("date", "")
    main_completed = result.get("main_completed", 0)
    main_total = result.get("main_total", 0)
    side_completed = result.get("side_completed", 0)
    side_total = result.get("side_total", 0)
    points_today = result.get("points_earned_today", 0)
    completed_tasks = result.get("completed_tasks") or []
    pending_tasks = result.get("pending_tasks") or []
    new_achievements = result.get("new_achievements") or []
    current_points = result.get("current_points", 0)
    level_title = result.get("level_title", "新手玩家")
    points_to_next = result.get("points_to_next_level")

    lines = [
        f"[结算数据卡片] {player_name or '---'} | {date or '今日'} | 主线{main_completed}/{main_total} | 支线{side_completed}/{side_total} | +{points_today}积分",
    ]

    if completed_tasks:
        lines.append("已通关: " + " | ".join(f"✓{t.get('name')}+{t.get('points',0)}" for t in completed_tasks))
    if pending_tasks:
        lines.append("待推进: " + " | ".join(f"○{t.get('name')}" for t in pending_tasks))
    if new_achievements:
        lines.append("新成就: " + " | ".join(a.get('name', '') for a in new_achievements))

    lines.append(f"状态: {current_points}积分 | {level_title}" + (f" | 距下一级{points_to_next}" if points_to_next else ""))

    return join_lines(lines)


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
