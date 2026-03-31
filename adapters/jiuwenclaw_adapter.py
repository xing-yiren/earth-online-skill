"""Minimal jiuwenclaw adapter skeleton.

This module defines the first concrete adapter target for Earth Online. It is
currently a non-invasive adapter and reads jiuwenclaw host files in a read-only
way when a local agent directory is available.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from adapters.base_adapter import BaseHostAdapter


class JiuwenclawAdapter(BaseHostAdapter):
    """Convert jiuwenclaw host data into standard host_context."""

    platform_name = "jiuwenclaw"

    def __init__(
        self, source: dict | None = None, agent_root: str | Path | None = None
    ) -> None:
        self.source = source or {}
        self.agent_root = (
            Path(agent_root) if agent_root else Path.home() / ".jiuwenclaw" / "agent"
        )
        self.memory_root = self.agent_root / "memory"
        self.user_file = self.memory_root / "USER.md"
        self.memory_file = self.memory_root / "MEMORY.md"
        self.messages_file = self.memory_root / "messages.json"

    def get_platform_info(self) -> dict:
        return {
            "platform": self.platform_name,
            "skill_runtime_version": "1.0",
        }

    def get_user_info(self) -> dict:
        user = self.source.get("user", {})
        file_user = self._load_user_from_file()
        return {
            "id": user.get("id")
            or self._slugify(file_user.get("user_name"))
            or "demo-user",
            "name": user.get("name") or file_user.get("user_name") or "DemoUser",
            "timezone": user.get("timezone")
            or file_user.get("timezone")
            or "Asia/Shanghai",
        }

    def get_session_info(self) -> dict:
        session = self.source.get("session", {})
        now = datetime.now().astimezone()
        return {
            "session_id": session.get("session_id"),
            "current_date": session.get("current_date", now.date().isoformat()),
            "current_time": session.get(
                "current_time", now.isoformat(timespec="seconds")
            ),
        }

    def get_intent_info(self, raw_input: str | None = None) -> dict:
        intent = self.source.get("intent", {})
        return {
            "name": intent.get("name", "unknown"),
            "confidence": intent.get("confidence"),
            "source_text": raw_input,
        }

    def get_context_info(self) -> dict:
        context = self.source.get("context", {})
        file_context = self._load_context_from_files()
        return {
            "recent_messages": context.get("recent_messages")
            or file_context["recent_messages"],
            "memory_facts": context.get("memory_facts") or file_context["memory_facts"],
            "preferences": context.get("preferences") or file_context["preferences"],
            "uncertainties": file_context["uncertainties"],
        }

    def get_runtime_info(self) -> dict:
        runtime = self.source.get("runtime", {})
        return {
            "trigger": runtime.get("trigger"),
            "locale": runtime.get("locale", "zh-CN"),
        }

    def _load_user_from_file(self) -> dict:
        if not self.user_file.exists():
            return {}

        content = self.user_file.read_text(encoding="utf-8")
        rows = {}
        for line in content.splitlines():
            match = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|", line)
            if not match:
                continue
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key in {"属性", "------"}:
                continue
            rows[key] = value

        note = rows.get("备注", "")
        user_name = rows.get("姓名") or None
        preferred_name = rows.get("昵称") or rows.get("称谓偏好") or None
        agent_aliases = self._extract_agent_aliases(note)

        if (
            not preferred_name
            and user_name
            and any(alias.lower() == user_name.lower() for alias in agent_aliases)
        ):
            preferred_name = None

        return {
            "user_name": user_name,
            "preferred_name": preferred_name,
            "timezone": rows.get("时区") or None,
            "language": rows.get("语言偏好") or None,
            "note": note or None,
            "agent_aliases": agent_aliases,
        }

    def _load_context_from_files(self) -> dict:
        return {
            "memory_facts": self._load_memory_facts(),
            "preferences": self._load_preferences(),
            "recent_messages": self._load_recent_messages(),
            "uncertainties": self._load_uncertainties(),
        }

    def _load_uncertainties(self) -> list[str]:
        user = self._load_user_from_file()
        uncertainties = []
        if not user.get("user_name"):
            uncertainties.append("user_name_missing")
        if user.get("agent_aliases") and not user.get("preferred_name"):
            uncertainties.append("user_name_may_conflict_with_agent_alias")
        if not user.get("timezone"):
            uncertainties.append("timezone_missing")
        return uncertainties

    def _load_memory_facts(self) -> list[str]:
        if not self.memory_file.exists():
            return []
        lines = self.memory_file.read_text(encoding="utf-8").splitlines()
        facts = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                facts.append(stripped[2:].strip())
        return facts[:10]

    def _load_preferences(self) -> list[str]:
        user = self._load_user_from_file()
        prefs = []
        if user.get("preferred_name"):
            prefs.append(f"preferred name: {user['preferred_name']}")
        if user.get("language"):
            prefs.append(f"language: {user['language']}")
        if user.get("note"):
            prefs.extend(
                self._sanitize_note_preferences(
                    user["note"], user.get("agent_aliases", [])
                )
            )
        return prefs[:10]

    def _load_recent_messages(self) -> list[str]:
        if not self.messages_file.exists():
            return []
        try:
            payload = json.loads(self.messages_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        records = payload.get("records", [])
        user_messages = [
            item.get("content", "")
            for item in records
            if item.get("role") == "user" and item.get("content")
        ]
        cleaned = [
            self._collapse_whitespace(item)
            for item in user_messages
            if self._is_useful_message(item)
        ]
        return cleaned[-8:]

    def _extract_agent_aliases(self, note: str) -> list[str]:
        if not note:
            return []
        aliases = re.findall(r"叫我\s+([A-Za-z0-9_-]+)", note)
        aliases.extend(
            re.findall(r"call me\s+([A-Za-z0-9_-]+)", note, flags=re.IGNORECASE)
        )
        aliases.extend(
            re.findall(r"call you\s+([A-Za-z0-9_-]+)", note, flags=re.IGNORECASE)
        )
        deduped = []
        for alias in aliases:
            if alias not in deduped:
                deduped.append(alias)
        return deduped

    def _sanitize_note_preferences(
        self, note: str, agent_aliases: list[str]
    ) -> list[str]:
        if not note:
            return []

        lowered = note.lower()
        noisy_markers = ["喜欢叫我", "call me", "call you", "your name is"]
        if any(marker in lowered for marker in noisy_markers):
            cleaned = re.sub(r"喜欢叫我[^，。,.!]*", "", note)
            cleaned = re.sub(
                r"can also call you[^，。,.!]*", "", cleaned, flags=re.IGNORECASE
            )
            cleaned = re.sub(
                r"your name is[^，。,.!]*", "", cleaned, flags=re.IGNORECASE
            )
            cleaned = self._collapse_whitespace(cleaned).strip(" ，。,.!")
            results = []
            if agent_aliases:
                results.append(f"agent aliases: {', '.join(agent_aliases)}")
            if cleaned:
                results.append(cleaned)
            return results
        return [note]

    def _is_useful_message(self, content: str) -> bool:
        stripped = self._collapse_whitespace(content)
        if len(stripped) < 4:
            return False
        trivial = {"ok", "okie", "stop", "looks good", "send it again", "wait"}
        return stripped.lower() not in trivial

    def _collapse_whitespace(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _slugify(self, value: str | None) -> str | None:
        if not value:
            return None
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
        return slug or None
