"""Daily settlement renderer."""

from __future__ import annotations

from ._format import join_lines, section


_TYPE_LABEL = {"main": "主线", "side": "支线"}


def render_daily_settlement(result: dict, player_name: str | None = None) -> str:
    if not result.get("success"):
        return _render_failure(result, default="结算失败。")

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

    header = "【地球 Online 每日结算】"
    if player_name and date:
        sub_header = f"玩家 {player_name}，{date} 副本结算如下："
    elif player_name:
        sub_header = f"玩家 {player_name}，今日副本结算如下："
    elif date:
        sub_header = f"{date} 副本结算如下："
    else:
        sub_header = "今日副本结算如下："

    summary_lines = [
        f"主线任务：{main_completed} / {main_total}",
        f"支线任务：{side_completed} / {side_total}",
        f"今日获得积分：{points_today}",
    ]

    completed_section = section(
        "已完成",
        [
            f"{item.get('name')}｜{_TYPE_LABEL.get(item.get('type'), '任务')}｜+{item.get('points', 0)}"
            for item in completed_tasks
        ],
        empty_hint="今天没有记录到已完成任务。",
    )

    pending_section = section(
        "仍待推进",
        [
            f"{item.get('name')}｜{_TYPE_LABEL.get(item.get('type'), '任务')}"
            for item in pending_tasks
        ],
        empty_hint="所有任务都清完了，今晚可以好好休息。",
    )

    achievement_lines = []
    if new_achievements:
        achievement_lines.append("【今日新成就】")
        for item in new_achievements:
            achievement_lines.append(f"- {item.get('name')}")

    state_lines = ["【当前状态】", f"积分：{current_points}", f"称号：{level_title}"]
    if points_to_next is not None:
        state_lines.append(f"距离下一级还差：{points_to_next} 积分")

    closing = _pick_closing(main_completed, side_completed, points_today)

    sections = [
        header,
        sub_header,
        "",
        "【完成情况】",
        *summary_lines,
        "",
        *completed_section,
        "",
        *pending_section,
    ]
    if achievement_lines:
        sections.append("")
        sections.extend(achievement_lines)
    sections.append("")
    sections.extend(state_lines)
    sections.append("")
    sections.append(closing)

    return join_lines(sections)


def _pick_closing(main_completed: int, side_completed: int, points_today: int) -> str:
    total = main_completed + side_completed
    if total == 0:
        return "今天没有结算到任务，但只要还在记录就不算掉线，明天再继续。"
    if points_today >= 100:
        return "今天推进的密度很高，注意收尾后让自己休息。"
    if main_completed > 0:
        return "主线推进到位，明天继续保持节奏。"
    return "支线打稳就是稳赢的一天，明天再挑一个主线试试。"


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
