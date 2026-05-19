"""Onboarding and initialization renderers."""

from __future__ import annotations

from ._format import join_lines


_FIELD_LABELS = {
    "name": "称呼",
    "timezone": "时区",
    "style": "表达风格",
    "morning_target_time": "晨间目标时间",
    "early_bird_grace_minutes": "早起宽限时间",
}


def render_init_profile(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="初始化检查失败。")

    if result.get("initialized"):
        profile = result.get("suggested_profile", {}) or {}
        lines = ["地球 Online 已经完成初始化，可以直接进入今日副本。"]
        if profile.get("name"):
            lines.append(f"当前玩家称呼：{profile['name']}")
        if profile.get("timezone"):
            lines.append(f"当前时区：{profile['timezone']}")
        lines.append("如果你愿意，我接下来也可以帮你从当前上下文整理一批可导入的候选任务。")
        return join_lines(lines)

    next_action = result.get("next_action")
    required_fields = result.get("required_fields") or []
    optional_fields = result.get("optional_fields") or []
    questions = result.get("recommended_questions") or []
    fallback = result.get("fallback_defaults", {}) or {}

    if next_action == "ask_required_fields":
        lines = [
            "首次进入地球 Online 前，需要先确认玩家档案。",
            "",
            "还需要确认：",
        ]
        for field in required_fields:
            label = _FIELD_LABELS.get(field, field)
            default = fallback.get(field)
            if default is not None:
                lines.append(f"- {label}（默认可用：{default}）")
            else:
                lines.append(f"- {label}")
        if questions:
            lines.append("")
            lines.append("建议先问：")
            lines.extend(f"- {question}" for question in questions)
        return join_lines(lines)

    if next_action == "ask_optional_fields":
        lines = ["玩家档案基本信息已具备，还可以确认偏好设置："]
        for field in optional_fields:
            lines.append(f"- {_FIELD_LABELS.get(field, field)}")
        if questions:
            lines.append("")
            lines.extend(f"- {question}" for question in questions)
        return join_lines(lines)

    profile = result.get("suggested_profile", {}) or {}
    return join_lines(
        [
            "玩家档案已具备，可以初始化地球 Online。",
            f"称呼：{profile.get('name') or fallback.get('name') or '玩家'}",
            f"时区：{profile.get('timezone') or fallback.get('timezone') or 'Asia/Shanghai'}",
            "确认后即可写入运行态配置。",
        ]
    )


def render_apply_init_config(result: dict) -> str:
    if not result.get("success"):
        error = result.get("error")
        if error == "confirmation_required":
            return "初始化需要用户明确确认后才能写入配置。请先确认称呼、时区和晨间设置。"
        if error == "required_fields_unresolved":
            unresolved = result.get("unresolved_fields") or []
            labels = [_FIELD_LABELS.get(field, field) for field in unresolved]
            return join_lines(
                [
                    "初始化还不能完成，仍有必填项未确认。",
                    f"待确认：{', '.join(labels)}",
                ]
            )
        return _render_failure(result, default="初始化配置写入失败。")

    profile = result.get("profile", {}) or {}
    return join_lines(
        [
            "地球 Online 玩家档案已初始化完成。",
            f"玩家称呼：{profile.get('name', '玩家')}",
            f"时区：{profile.get('timezone', 'Asia/Shanghai')}",
            f"表达风格：{profile.get('style', 'standard')}",
            f"晨间目标：{profile.get('morning_target_time', '07:00')} + {profile.get('early_bird_grace_minutes', 30)} 分钟宽限",
            "如果你愿意，我接下来可以继续帮你从当前上下文整理可导入的候选任务。",
        ]
    )


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
