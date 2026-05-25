"""Renderers for optional onboarding task imports."""

from __future__ import annotations

from ._format import join_lines


_TYPE_LABEL = {"main": "主线", "side": "支线"}
_SOURCE_LABEL = {
    "conversation": "当前对话",
    "memory": "长期记忆",
    "todo": "TODO",
    "plan": "计划",
    "manual": "手动输入",
    "session_scan": "跨会话扫描",
}


def render_suggest_onboarding_imports(result: dict) -> str:
    if not result.get("success"):
        error = result.get("error")
        if error == "confirmation_required":
            return result.get("message", "需要用户确认后才能继续。")
        return _render_failure(result, default="候选任务生成失败。")

    candidates = result.get("candidates") or []
    if not candidates:
        return "[候选导入] 暂无候选 | 可直接描述想加入的任务"

    items = []
    for index, candidate in enumerate(candidates, 1):
        source = _SOURCE_LABEL.get(candidate.get("source"), candidate.get("source", "未知来源"))
        items.append(f"{index}.{candidate.get('name')}({_TYPE_LABEL.get(candidate.get('type'), '任务')}/{candidate.get('points', 0)}积分/{source})")

    return f"[候选导入] 共{len(items)}条 | " + " | ".join(items) + " | 回复编号导入或'都不要'"


def render_apply_onboarding_imports(result: dict) -> str:
    if not result.get("success"):
        error = result.get("error")
        if error == "no_candidates_selected":
            return "还没有收到需要导入的候选任务。请先确认要导入哪些编号。"
        return _render_failure(result, default="候选任务导入失败。")

    imported = result.get("imported") or []
    skipped = result.get("skipped") or []

    lines = [f"[导入完成] 已导入{len(imported)}条"]
    if imported:
        lines.append("导入: " + " | ".join(f"{i.get('name')}({i.get('points', 0)}积分)" for i in imported))
    if skipped:
        lines.append("跳过: " + " | ".join(s.get('name', '?') for s in skipped))

    return join_lines(lines)


def _render_failure(result: dict, default: str) -> str:
    message = result.get("message")
    if message:
        return f"{default}\n原因：{message}"
    return default
