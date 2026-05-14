"""Shared helpers for renderers."""

from __future__ import annotations


def join_lines(lines: list[str]) -> str:
    """Join non-empty lines with single newlines, trimming edges."""

    return "\n".join(line for line in lines if line is not None).strip()


def section(title: str, items: list[str], empty_hint: str | None = None) -> list[str]:
    """Render a titled bullet section.

    Returns a list of lines (no trailing newline), so callers can compose
    multiple sections with join_lines.
    """

    lines = [f"【{title}】"]
    if items:
        lines.extend(f"- {item}" for item in items)
    elif empty_hint is not None:
        lines.append(empty_hint)
    return lines


def format_points(value: int | None) -> str:
    if value is None:
        return "0"
    return str(value)


def safe_name(name: str | None, fallback: str = "玩家") -> str:
    if not name:
        return fallback
    return name
