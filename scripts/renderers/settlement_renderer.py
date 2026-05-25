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
        "╔══════════════════════════╗",
        "║     副本结算 · 战报       ║",
        "╚══════════════════════════╝",
        "",
        f"  {player_name or '---'}，副本结算如下：",
        f"  日期：{date}" if date else "  日期：今日",
        "",
        "▸ 结算中...",
        "▸ 战报生成 ✓",
        "",
        "  ── 任务推进 ──",
        f"  主线通关：{main_completed} / {main_total}",
        f"  支线通关：{side_completed} / {side_total}",
        f"  今日获得积分：+{points_today}",
    ]

    # Completed
    lines.append("")
    lines.append("  ── 已通关 ──")
    if completed_tasks:
        for item in completed_tasks:
            t = _TYPE_LABEL.get(item.get('type'), '任务')
            lines.append(f"  ✓ {item.get('name')}｜{t}｜+{item.get('points', 0)} 积分")
    else:
        lines.append("  （今日无通关记录）")

    # Pending
    lines.append("")
    lines.append("  ── 仍待推进 ──")
    if pending_tasks:
        for item in pending_tasks:
            lines.append(f"  ○ {item.get('name')}｜{_TYPE_LABEL.get(item.get('type'), '任务')}")
    else:
        lines.append("  所有任务已清完，今晚安心休息。")

    # Achievements
    if new_achievements:
        lines.append("")
        lines.append("  ── 今日新成就 ──")
        for item in new_achievements:
            lines.append(f"  ★ {item.get('name')}")

    # Status
    lines.append("")
    lines.append("  ── 当前状态 ──")
    lines.append(f"  积分：{current_points}")
    lines.append(f"  称号：{level_title}")
    if points_to_next is not None:
        lines.append(f"  距离下一级：{points_to_next} 积分")

    lines.append("")
    lines.append(_pick_closing(main_completed, side_completed, points_today))

    return join_lines(lines)


def _pick_closing(main_completed: int, side_completed: int, points_today: int) -> str:
    total = main_completed + side_completed
    if total == 0:
        return "今天没有结算到任务，但只要还在记录就不算掉线——明天继续。"
    if points_today >= 100:
        return "今天推进密度很高，注意收尾后让自己休息。明天副本见。"
    if main_completed > 0:
        return "主线推进到位，明天继续保持节奏。"
    return "支线打稳就是稳赢的一天，明天挑个主线试试。"


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
