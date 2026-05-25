"""Morning brief and check-in renderers - game-style dungeon entrance."""

from __future__ import annotations

from ._format import join_lines, safe_name


def render_morning_brief(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="⚠ 今日副本开启失败，系统异常。")

    player = safe_name(result.get("player_name"))
    date = result.get("date", "")
    survival_days = result.get("survival_days", 0)
    streak = result.get("early_bird_streak", 0)
    main_tasks = result.get("main_tasks") or []
    side_tasks = result.get("side_tasks") or []
    current_points = result.get("current_points", 0)
    level_title = result.get("level_title", "新手玩家")

    lines = [
        f"[晨间数据卡片] {player} | 生存第{survival_days}天 | 连续签到{streak}天 | {level_title} | {current_points}积分",
        f"日期: {date}" if date else "",
    ]

    if main_tasks:
        lines.append("主线: " + " | ".join(_format_main(t) for t in main_tasks))
    else:
        lines.append("主线: 暂无")
    if side_tasks:
        lines.append("支线: " + " | ".join(_format_side(t) for t in side_tasks))
    else:
        lines.append("支线: 暂无")

    return join_lines(lines)


def render_morning_checkin(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="⚠ 晨间签到失败，请稍后再试。")

    is_early = result.get("is_early_bird", False)
    already = result.get("already_recorded", False)
    stats = result.get("stats", {}) or {}
    streak = stats.get("early_bird_streak", 0)
    best = stats.get("best_early_bird_streak", streak)
    unlocked = result.get("unlocked") or []

    status = "已签到(重复)" if already else ("早起窗口 ✓" if is_early else "已记录(非早起窗口)")
    lines = [f"[签到数据卡片] {status} | 连续早起{streak}天 | 历史最佳{best}天"]

    if unlocked:
        achievement_info = " | ".join(f"{a.get('name')}(+{a.get('reward_points', 0)})" for a in unlocked)
        lines.append(f"新成就: {achievement_info}")

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
        suffix = " [✓ 今日已完成]"
    elif completed is False:
        suffix = " [待打卡]"
    return f"{name}｜{points} 积分{suffix}"


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
