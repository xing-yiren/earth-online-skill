"""Task-related renderers - game-style quest feedback."""

from __future__ import annotations

from ._format import join_lines


_TYPE_LABEL = {"main": "主线", "side": "支线"}
_RECURRENCE_LABEL = {"once": "一次性", "daily": "每日"}
_TYPE_ICON = {"main": "◈", "side": "◇"}


def render_task_created(result: dict) -> str:
    if not result.get("success"):
        return _render_create_failure(result)

    task = result.get("task", {}) or {}
    name = task.get("name", "未命名任务")
    task_type = task.get("type", "main")
    type_label = _TYPE_LABEL.get(task_type, "任务")
    icon = _TYPE_ICON.get(task_type, "•")
    recurrence = _RECURRENCE_LABEL.get(task.get("recurrence"), "")
    points = task.get("points", 0)
    deadline = task.get("deadline")

    lines = [
        "▸ 任务登记成功 ✓",
        "",
        f"  {icon} {name}",
        f"  类型：{type_label}",
        f"  奖励：{points} 积分",
    ]
    if recurrence:
        lines.append(f"  频率：{recurrence}")
    if deadline:
        lines.append(f"  截止：{deadline}")

    if task.get("type") == "side" and task.get("recurrence") == "daily":
        lines.extend(["", "这条支线会保留在每日副本里，从今天开始。完成时告诉我即可打卡。"])
    else:
        lines.extend(["", '完成后告诉我"XX 做完了"，帮你结算积分。'])

    return join_lines(lines)


def render_task_completed(result: dict) -> str:
    if not result.get("success"):
        return _render_complete_failure(result)

    task = result.get("task", {}) or {}
    name = task.get("name", "未命名任务")
    task_type = task.get("type", "main")
    icon = _TYPE_ICON.get(task_type, "•")
    transaction = result.get("task_points_transaction", {}) or {}
    points_earned = transaction.get("amount", task.get("points", 0))
    stats = result.get("points_stats", {}) or {}
    current_points = stats.get("available_points", 0)
    level_title = stats.get("level_title", "新手玩家")
    points_to_next = stats.get("points_to_next_level")
    unlocked = result.get("unlocked_achievements") or []

    lines = [
        "▸ 任务通关 ✓",
        "",
        f"  {icon} {name}",
        f"  奖励积分：+{points_earned}",
    ]

    if unlocked:
        lines.append("")
        lines.append("  ── 同时解锁成就 ──")
        for achievement in unlocked:
            lines.append(f"  ★ {achievement.get('name', '未知')}：{achievement.get('reason', '')}（+{achievement.get('reward_points', 0)} 积分）")

    lines.append("")
    lines.append("  ── 当前状态 ──")
    lines.append(f"  积分：{current_points}")
    lines.append(f"  称号：{level_title}")
    if points_to_next is not None:
        lines.append(f"  距离下一级：{points_to_next} 积分")
    lines.append("")
    lines.append("今日推进 +1，节奏稳住。")

    return join_lines(lines)


def render_active_tasks(tasks: list[dict]) -> str:
    if not tasks:
        return join_lines([
            "▸ 当前没有进行中的任务",
            "",
            '  可以说"我今天要做 XXX"登记主线，',
            '  或"以后每天 XXX"登记支线习惯。',
        ])

    main_items = []
    side_items = []
    for task in tasks:
        line = _format_active_task(task)
        if task.get("type") == "main":
            main_items.append(f"  ◈ {line}")
        elif task.get("type") == "side":
            side_items.append(f"  ◇ {line}")

    lines = ["▸ 当前任务列表", ""]

    lines.append("  ── 主线任务 ──")
    if main_items:
        lines.extend(main_items)
    else:
        lines.append("  （暂无）")

    lines.append("")
    lines.append("  ── 支线任务 ──")
    if side_items:
        lines.extend(side_items)
    else:
        lines.append("  （暂无）")

    return join_lines(lines)


def render_task_updated(result: dict) -> str:
    if not result.get("success"):
        return _render_generic_failure(result, default="⚠ 任务更新失败。")

    task = result.get("task", {}) or {}
    changed = result.get("changed_fields") or []
    name = task.get("name", "未命名任务")
    points = task.get("points", 0)
    deadline = task.get("deadline")

    lines = [
        "▸ 任务已更新 ✓",
        "",
        f"  任务：{name}",
    ]
    if changed:
        lines.append(f"  变更：{', '.join(changed)}")
    lines.append(f"  奖励：{points} 积分")
    if deadline:
        lines.append(f"  截止：{deadline}")

    return join_lines(lines)


def render_task_cancelled(result: dict) -> str:
    if not result.get("success"):
        return _render_generic_failure(result, default="⚠ 任务取消失败。")

    task = result.get("task", {}) or {}
    name = task.get("name", "未命名任务")
    return join_lines([
        f"▸ 已取消任务：{name}",
        "如果误操作，直接说重新创建一个同名任务即可。",
    ])


def _format_active_task(task: dict) -> str:
    name = task.get("name", "未命名任务")
    points = task.get("points", 0)
    recurrence = task.get("recurrence")
    deadline = task.get("deadline")
    last_completed = task.get("last_completed_date")

    text = f"{name}｜{points} 积分"
    if recurrence == "daily":
        if last_completed:
            text += f"｜每日，上次完成 {last_completed}"
        else:
            text += "｜每日，尚未打卡"
    if deadline:
        text += f"｜截止 {deadline}"
    return text


def _render_create_failure(result: dict) -> str:
    error = result.get("error")
    if error == "duplicate_task":
        existing = result.get("task") or {}
        existing_name = existing.get("name", "")
        return join_lines([
            f"▸ 已经存在相似的进行中任务：【{existing_name}】。",
            '如果想替换或修改，可以告诉我"把这个任务改成 XXX"，否则我就保留原任务。',
        ])
    if error == "invalid_task_name":
        return "▸ 任务名称不能为空，请再描述一下今天要做的事。"
    if error == "invalid_task_type":
        return "▸ 任务类型只能是主线或支线，需要重新确认一下。"
    if error == "invalid_recurrence":
        return "▸ 任务频率只能是一次性或每日，需要重新确认一下。"
    return _render_generic_failure(result, default="⚠ 任务创建失败。")


def _render_complete_failure(result: dict) -> str:
    error = result.get("error")
    if error == "task_not_found":
        return join_lines([
            "▸ 没有找到匹配的进行中任务。",
            "可以选择：",
            "  1. 先把它登记为新任务再完成",
            "  2. 换一个更具体的任务名称",
            "  3. 查看当前任务列表",
        ])
    if error == "needs_confirmation":
        candidates = result.get("candidates") or []
        lines = ["▸ 匹配到多个任务，请确认是哪一条："]
        for index, candidate in enumerate(candidates, 1):
            lines.append(f"  {index}. {candidate.get('name')}｜{_TYPE_LABEL.get(candidate.get('type'), '任务')}")
        return join_lines(lines)
    if error == "task_already_completed":
        task = result.get("task") or {}
        return f"▸ 任务【{task.get('name', '未命名任务')}】之前已经完成过了，不会重复加分。"
    if error == "task_already_completed_today":
        task = result.get("task") or {}
        return f"▸ 今天已经完成过【{task.get('name', '未命名任务')}】了，明天再来打卡。"
    return _render_generic_failure(result, default="⚠ 任务完成失败。")


def _render_generic_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
