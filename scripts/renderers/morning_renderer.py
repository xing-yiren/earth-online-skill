"""Morning brief and check-in renderers."""

from __future__ import annotations

from ._format import join_lines, safe_name, section


def render_morning_brief(result: dict) -> str:
    """Turn get_morning_brief result into a natural reply."""

    if not result.get("success"):
        return _render_failure(result, default="今日副本暂时无法开启。")

    player = safe_name(result.get("player_name"))
    date = result.get("date", "")
    survival_days = result.get("survival_days", 0)
    streak = result.get("early_bird_streak", 0)
    main_tasks = result.get("main_tasks") or []
    side_tasks = result.get("side_tasks") or []
    current_points = result.get("current_points", 0)
    level_title = result.get("level_title", "新手玩家")

    header = f"早上好，玩家 {player}。"
    if date:
        header += f"\n今日副本已开启（{date}）。"
    else:
        header += "\n今日副本已开启。"

    status_lines = [
        f"生存记录：{survival_days} 天",
        f"连续晨间签到：{streak} 天",
        f"当前称号：{level_title}",
        f"当前积分：{current_points}",
    ]

    main_items = [_format_main(task) for task in main_tasks]
    side_items = [_format_side(task) for task in side_tasks]

    main_section = section(
        "今日主线",
        main_items,
        empty_hint="暂无主线任务。可以直接说“我今天要完成 XXX”，我会帮你登记。",
    )
    side_section = section(
        "今日支线",
        side_items,
        empty_hint="暂无支线任务。可以挑一个想坚持的习惯，比如阅读、运动、冥想。",
    )

    encouragement = _pick_encouragement(main_tasks, side_tasks)

    return join_lines(
        [
            header,
            "",
            *status_lines,
            "",
            *main_section,
            "",
            *side_section,
            "",
            encouragement,
        ]
    )


def render_morning_checkin(result: dict) -> str:
    """Turn record_morning_checkin result into a natural reply."""

    if not result.get("success"):
        return _render_failure(result, default="晨间签到失败，请稍后再试。")

    is_early = result.get("is_early_bird", False)
    already = result.get("already_recorded", False)
    stats = result.get("stats", {}) or {}
    streak = stats.get("early_bird_streak", 0)
    best = stats.get("best_early_bird_streak", streak)

    unlocked = result.get("unlocked") or []

    if already:
        lines = [
            "今天已经完成过晨间签到了。",
            f"当前连续早起：{streak} 天（历史最佳：{best}）。",
        ]
    elif is_early:
        lines = [
            "晨间签到成功，进入早起窗口。",
            f"当前连续早起：{streak} 天（历史最佳：{best}）。",
        ]
    else:
        lines = [
            "签到已记录。本次未落在早起窗口内，今天的早起 streak 不会增加。",
            f"当前连续早起：{streak} 天（历史最佳：{best}）。",
        ]

    if unlocked:
        lines.append("")
        lines.append("【新解锁成就】")
        for item in unlocked:
            lines.append(f"- {item.get('name')}：{item.get('reason')}（+{item.get('reward_points', 0)} 积分）")

    return join_lines(lines)


def _format_main(task: dict) -> str:
    name = task.get("name", "未命名任务")
    points = task.get("points", 0)
    deadline = task.get("deadline")
    text = f"{name}｜{points} 积分"
    if deadline:
        text += f"｜截止 {deadline}"
    return text


def _format_side(task: dict) -> str:
    name = task.get("name", "未命名任务")
    points = task.get("points", 0)
    completed = task.get("completed_today")
    suffix = ""
    if completed is True:
        suffix = "（今日已完成）"
    elif completed is False:
        suffix = "（今日待打卡）"
    return f"{name}｜{points} 积分{suffix}"


def _pick_encouragement(main_tasks: list, side_tasks: list) -> str:
    if not main_tasks and not side_tasks:
        return "今天可以从一件小事开始，先把节奏起出来。"
    if main_tasks:
        return "今天的目标不需要完美通关，先推进一个主线任务就算开局成功。"
    return "今天没有重磅主线，把支线打稳就是稳赢的一天。"


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
