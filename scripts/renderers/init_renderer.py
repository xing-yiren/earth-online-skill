"""Onboarding and initialization renderers — game-style character creation."""

from __future__ import annotations

from ._format import join_lines


_FIELD_LABELS = {
    "name": "玩家称号",
    "timezone": "时区",
    "style": "表达风格",
    "morning_target_time": "晨间目标时间",
    "early_bird_grace_minutes": "早起宽限",
}


def render_init_profile(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="⚠ 系统启动异常，初始化检查未通过。")

    if result.get("initialized"):
        profile = result.get("suggested_profile", {}) or {}
        name = profile.get("name", "玩家")
        tz = profile.get("timezone", "---")
        return join_lines([
            "▸ 地球 Online 系统已就绪",
            "",
            f"  当前登录玩家：{name}",
            f"  所在时区：{tz}",
            "",
            "系统自检完成，可以进入今日副本。",
        ])

    next_action = result.get("next_action")
    required_fields = result.get("required_fields") or []
    fallback = result.get("fallback_defaults", {}) or {}
    questions = result.get("recommended_questions") or []

    if next_action == "ask_required_fields":
        return _render_character_create(required_fields, fallback, questions)

    if next_action == "ask_optional_fields":
        optional_fields = result.get("optional_fields") or []
        return _render_optional_config(optional_fields, questions)

    profile = result.get("suggested_profile", {}) or {}
    return join_lines([
        "▸ 玩家档案已就绪",
        "",
        f"  称号：{profile.get('name') or fallback.get('name') or '玩家'}",
        f"  时区：{profile.get('timezone') or fallback.get('timezone') or 'Asia/Shanghai'}",
        "",
        "确认后系统将写入运行态配置。",
    ])


def _render_character_create(required_fields: list[str], fallback: dict, questions: list[str]) -> str:
    lines = [
        "╔══════════════════════════╗",
        "║   地球 Online · 玩家建档  ║",
        "╚══════════════════════════╝",
        "",
        "▸ 系统自检中...",
        "▸ 检测到新玩家，启动建档流程...",
        "",
        "请确认以下档案信息：",
        "",
    ]
    field_index = 1
    for field in required_fields:
        label = _FIELD_LABELS.get(field, field)
        default = fallback.get(field, "---")
        lines.append(f"  [{field_index}] {label}：___________（系统检测默认：{default}）")
        field_index += 1

    if questions:
        lines.append("")
        lines.append('你可以逐项回复修改，也可以直接说"确认"使用系统默认值。')
    else:
        lines.append("")
        lines.append("请回复确认，或指出需要修改的项目编号和值。")

    return join_lines(lines)


def _render_optional_config(optional_fields: list[str], questions: list[str]) -> str:
    lines = [
        "▸ 基础档案已确认",
        "",
        "以下为可选偏好设置，可以直接跳过：",
        "",
    ]
    for field in optional_fields:
        lines.append(f"  - {_FIELD_LABELS.get(field, field)}")
    if questions:
        lines.append("")
        lines.extend(f"  ? {q}" for q in questions)
    return join_lines(lines)


def render_apply_init_config(result: dict) -> str:
    if not result.get("success"):
        error = result.get("error")
        if error == "confirmation_required":
            return "⚠ 档案写入需要玩家确认后才能执行。请先确认你的称号、时区和晨间设置。"
        if error == "required_fields_unresolved":
            unresolved = result.get("unresolved_fields") or []
            labels = [_FIELD_LABELS.get(field, field) for field in unresolved]
            return join_lines([
                "⚠ 档案不完整，仍有必填项未确认。",
                f"  待确认：{', '.join(labels)}",
                "",
                "请补充以上信息后重新提交。",
            ])
        return _render_failure(result, default="⚠ 档案写入失败，系统异常。")

    profile = result.get("profile", {}) or {}
    name = profile.get("name", "玩家")
    tz = profile.get("timezone", "Asia/Shanghai")
    morning = profile.get("morning_target_time", "07:00")
    grace = profile.get("early_bird_grace_minutes", 30)

    return join_lines([
        "╔══════════════════════════╗",
        "║     玩家档案 · 创建完成   ║",
        "╚══════════════════════════╝",
        "",
        "▸ 正在写入玩家数据...",
        "▸ 写入完成 ✓",
        "",
        f"  玩家称号：{name}",
        f"  时区：{tz}",
        f"  晨间签到窗口：{morning} ± {grace} min",
        "",
        "系统就绪，接下来进入任务导入环节。",
    ])


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
