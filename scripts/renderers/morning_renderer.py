"""Morning brief and check-in renderers - game-style dungeon entrance."""

from __future__ import annotations

from ._format import join_lines, safe_name, section


def render_morning_brief(result: dict) -> str:
    """Turn get_morning_brief result into a game-style morning briefing."""

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

    day_label = "首次登录" if survival_days <= 1 else f"累计 {survival_days} 天"

    lines = [
        f"叮！亲爱的 {player} 玩家，早上好！",
        "",
        f"恭喜你通过昨日生存关卡，当前累计登录：{day_label}。",
        f"连续早起签到：{streak} 天",
        "",
        "▸ 今日副本正在开启...",
        "▸ 主线 / 支线任务已刷新 ✓",
        "",
        f"  当前称号：{level_title}",
        f"  当前积分：{current_points}",
    ]

    main_items = [_format_main(task) for task in main_tasks]
    side_items = [_format_side(task) for task in side_tasks]

    lines.append("")
    lines.append("  ── 主线任务 ──")
    if main_items:
        lines.extend(f"  ◈ {item}" for item in main_items)
    else:
        lines.append('  （暂无）说"我今天要完成 XXX"即可登记主线。')

    lines.append("")
    lines.append("  ── 支线任务 ──")
    if side_items:
        lines.extend(f"  ◇ {item}" for item in side_items)
    else:
        lines.append("  （暂无）可挑一个想坚持的习惯，如阅读、运动、冥想。")

    lines.append("")
    lines.append(_pick_closing(main_tasks, side_tasks))

    return join_lines(lines)


def render_morning_checkin(result: dict) -> str:
    """Turn record_morning_checkin result into a game-style check-in report."""

    if not result.get("success"):
        return _render_failure(result, default="⚠ 晨间签到失败，请稍后再试。")

    is_early = result.get("is_early_bird", False)
    already = result.get("already_recorded", False)
    stats = result.get("stats", {}) or {}
    streak = stats.get("early_bird_streak", 0)
    best = stats.get("best_early_bird_streak", streak)
    unlocked = result.get("unlocked") or []

    if already:
        lines = [
            "▸ 今日已签到，每日奖励已领取",
            "",
            f"  连续早起：{streak} 天 ｜ 历史最佳：{best} 天",
        ]
    elif is_early:
        lines = [
            "▸ 晨间签到成功 ✓",
            "▸ 已进入早起窗口，每日登录奖励已发放",
            "",
            f"  连续早起：{streak} 天 ｜ 历史最佳：{best} 天",
        ]
    else:
        lines = [
            "▸ 签到已记录",
            "▸ 本次未落在早起窗口内，streak 保持不变",
            "",
            f"  连续早起：{streak} 天 ｜ 历史最佳：{best} 天",
        ]

    if unlocked:
        lines.append("")
        lines.append("  ── 新解锁成就 ──")
        for item in unlocked:
            lines.append(f"  ★ {item.get('name')}：{item.get('reason')}（+{item.get('reward_points', 0)} 积分）")

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


def _pick_closing(main_tasks: list, side_tasks: list) -> str:
    if not main_tasks and not side_tasks:
        return "今天从一件小事开始，先把节奏起出来。主线或支线，开局就是胜利。"
    if main_tasks:
        return "今日副本已开启，祝玩家通关顺利。"
    return "没有重磅主线，把支线打稳也是稳赢的一天。"


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
