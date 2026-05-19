"""Renderers for optional onboarding task imports."""

from __future__ import annotations

from ._format import join_lines, section


_TYPE_LABEL = {"main": "主线", "side": "支线"}
_SOURCE_LABEL = {
    "conversation": "当前对话",
    "memory": "长期记忆",
    "todo": "TODO",
    "plan": "计划",
    "manual": "手动输入",
}


def render_suggest_onboarding_imports(result: dict) -> str:
    if not result.get("success"):
        return _render_failure(result, default="候选任务生成失败。")

    candidates = result.get("candidates") or []
    if not candidates:
        return join_lines(
            [
                "当前没有生成可导入的任务候选。",
                "你可以直接告诉我几条想导入的任务，或者稍后再手动创建。",
            ]
        )

    items = []
    for index, candidate in enumerate(candidates, 1):
        source = _SOURCE_LABEL.get(candidate.get("source"), candidate.get("source", "未知来源"))
        items.append(
            f"{index}. {candidate.get('name')}｜{_TYPE_LABEL.get(candidate.get('type'), '任务')}｜"
            f"{candidate.get('points', 0)} 积分｜来源：{source}"
        )

    return join_lines(
        [
            "我已整理出一批可导入的候选任务。",
            "这些候选还没有写入你的副本任务列表。",
            "",
            *section("候选任务", items),
            "",
            "如果你想导入其中几项，请回复编号；如果都不要，可以直接说“都不要”。",
        ]
    )


def render_apply_onboarding_imports(result: dict) -> str:
    if not result.get("success"):
        error = result.get("error")
        if error == "no_candidates_selected":
            return "还没有收到需要导入的候选任务。请先确认要导入哪些编号。"
        return _render_failure(result, default="候选任务导入失败。")

    imported = result.get("imported") or []
    skipped = result.get("skipped") or []

    lines = []
    if imported:
        lines.append(f"已导入 {len(imported)} 条任务：")
        lines.extend(f"- {item.get('name')}｜{item.get('points', 0)} 积分" for item in imported)
    else:
        lines.append("这次没有成功导入任何任务。")

    if skipped:
        lines.append("")
        lines.append("以下候选未导入：")
        for item in skipped:
            reason = item.get("error") or "unknown_error"
            lines.append(f"- {item.get('name', '未命名候选')}｜原因：{reason}")

    if imported:
        lines.append("")
        lines.append("玩家档案和初始任务都已准备好，你可以直接开始今日副本。")
    return join_lines(lines)


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
