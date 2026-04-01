"""Initialization and onboarding service for Earth Online skill."""

from __future__ import annotations

import json
import re
from datetime import datetime

from .config import (
    DEFAULT_PLAYER_NAME,
    DEFAULT_STYLE,
    DEFAULT_TIMEZONE,
    INIT_STATE_FILE,
    USER_FILE,
    ensure_data_root,
)


class InitService:
    """Prepare and apply runtime profile initialization."""

    def __init__(self) -> None:
        ensure_data_root()

    def init_skill_profile(self, payload: dict) -> dict:
        host_context = payload.get("host_context", {})
        initialized = self.is_initialized()
        current_profile = self._load_user_profile()
        context_uncertainties = host_context.get("context", {}).get("uncertainties", [])

        trusted_name = host_context.get("user", {}).get("name")
        if not trusted_name and initialized:
            trusted_name = current_profile["name"]
        if "user_name_missing" in context_uncertainties:
            trusted_name = None

        trusted_timezone = host_context.get("user", {}).get("timezone")
        if not trusted_timezone and initialized:
            trusted_timezone = current_profile["timezone"]
        if "timezone_missing" in context_uncertainties:
            trusted_timezone = None

        fallback_defaults = {
            "name": DEFAULT_PLAYER_NAME,
            "timezone": DEFAULT_TIMEZONE,
            "style": current_profile["style"] or DEFAULT_STYLE,
            "morning_target_time": current_profile["morning_target_time"] or "07:00",
            "early_bird_grace_minutes": int(
                current_profile["early_bird_grace_minutes"] or 30
            ),
        }

        suggested_profile = {
            "user_id": host_context.get("user", {}).get("id") or "demo-user",
            "name": trusted_name,
            "timezone": trusted_timezone,
            "style": self._pick_style(host_context, current_profile),
            "morning_target_time": fallback_defaults["morning_target_time"],
            "early_bird_grace_minutes": fallback_defaults["early_bird_grace_minutes"],
        }

        required_fields = []
        optional_fields = []
        defaulted_fields = []
        recommended_questions = []
        if (
            not host_context.get("user", {}).get("name")
            or "user_name_missing" in context_uncertainties
        ):
            required_fields.append("name")
            recommended_questions.append("你希望我怎么称呼你？")
        if (
            not host_context.get("user", {}).get("timezone")
            or "timezone_missing" in context_uncertainties
        ):
            required_fields.append("timezone")
            recommended_questions.append("你的时区是什么？")
        if "user_name_may_conflict_with_agent_alias" in context_uncertainties:
            if "name" not in required_fields:
                required_fields.append("name")
            recommended_questions.append(
                "我目前还不确定你的称呼，想确认一下我应该怎么称呼你？"
            )
        if not current_profile["morning_target_time"]:
            required_fields.append("morning_target_time")
            recommended_questions.append("默认几点算你的晨间目标时间？")
        if not current_profile["early_bird_grace_minutes"]:
            required_fields.append("early_bird_grace_minutes")
            recommended_questions.append("早起宽限几分钟比较合适？")
        if not current_profile["style"]:
            optional_fields.append("style")
            recommended_questions.append("你更喜欢轻度、标准还是热血一点的表达风格？")

        if (
            not host_context.get("user", {}).get("name")
            or "user_name_missing" in context_uncertainties
        ):
            defaulted_fields.append("name")
        if (
            not host_context.get("user", {}).get("timezone")
            or "timezone_missing" in context_uncertainties
        ):
            defaulted_fields.append("timezone")
        if not current_profile["style"]:
            defaulted_fields.append("style")
        if not current_profile["morning_target_time"]:
            defaulted_fields.append("morning_target_time")
        if not current_profile["early_bird_grace_minutes"]:
            defaulted_fields.append("early_bird_grace_minutes")

        next_action = "ready"
        if initialized:
            next_action = "skip_onboarding"
        elif required_fields:
            next_action = "ask_required_fields"
        elif optional_fields:
            next_action = "ask_optional_fields"

        return {
            "success": True,
            "initialized": initialized,
            "suggested_profile": suggested_profile,
            "required_fields": required_fields,
            "optional_fields": optional_fields,
            "defaulted_fields": defaulted_fields,
            "recommended_questions": recommended_questions,
            "next_action": next_action,
            "context_uncertainties": context_uncertainties,
            "fallback_defaults": fallback_defaults,
        }

    def apply_init_config(self, payload: dict) -> dict:
        confirmed_by_user = payload.get("confirmed_by_user", False)
        confirmed_fields = payload.get("confirmed_fields") or []
        required_fields = payload.get("required_fields") or []

        if not confirmed_by_user:
            return {
                "success": False,
                "error": "confirmation_required",
                "message": "Required onboarding fields must be explicitly confirmed by the user before initialization can be applied.",
            }

        unresolved_fields = [
            field for field in required_fields if field not in confirmed_fields
        ]
        if unresolved_fields:
            return {
                "success": False,
                "error": "required_fields_unresolved",
                "message": "Some required onboarding fields have not been confirmed yet.",
                "unresolved_fields": unresolved_fields,
            }

        profile = {
            "user_id": payload.get("user_id") or "demo-user",
            "name": payload.get("name") or DEFAULT_PLAYER_NAME,
            "timezone": payload.get("timezone") or DEFAULT_TIMEZONE,
            "style": payload.get("style") or DEFAULT_STYLE,
            "morning_broadcast": payload.get("morning_broadcast") or "07:00",
            "evening_settlement": payload.get("evening_settlement") or "22:00",
            "broadcast_channel": payload.get("broadcast_channel") or "webchat",
            "morning_target_time": payload.get("morning_target_time") or "07:00",
            "early_bird_grace_minutes": int(
                payload.get("early_bird_grace_minutes") or 30
            ),
            "track_habits": bool(payload.get("track_habits", True)),
            "habit_list": payload.get("habit_list") or ["晨跑", "阅读", "冥想"],
        }

        USER_FILE.write_text(self._render_user_profile(profile), encoding="utf-8")
        self._write_init_state(profile)

        return {
            "success": True,
            "initialized": True,
            "runtime_data_root": str(USER_FILE.parent),
            "profile": {
                "user_id": profile["user_id"],
                "name": profile["name"],
                "timezone": profile["timezone"],
                "style": profile["style"],
                "morning_target_time": profile["morning_target_time"],
                "early_bird_grace_minutes": profile["early_bird_grace_minutes"],
            },
            "confirmed_fields": confirmed_fields,
        }

    def is_initialized(self) -> bool:
        return INIT_STATE_FILE.exists()

    def _load_user_profile(self) -> dict:
        content = USER_FILE.read_text(encoding="utf-8") if USER_FILE.exists() else ""
        return {
            "name": self._extract_field(content, "name"),
            "timezone": self._extract_field(content, "timezone"),
            "style": self._extract_field(content, "style"),
            "morning_target_time": self._extract_field(content, "morning_target_time"),
            "early_bird_grace_minutes": self._extract_field(
                content, "early_bird_grace_minutes"
            ),
        }

    def _pick_style(self, host_context: dict, current_profile: dict) -> str:
        preferences = host_context.get("context", {}).get("preferences", [])
        normalized = " ".join(str(item) for item in preferences).lower()
        if "热血" in normalized or "rpg" in normalized:
            return "hardcore"
        if "轻" in normalized:
            return "light"
        return current_profile["style"] or DEFAULT_STYLE

    def _write_init_state(self, profile: dict) -> None:
        state = {
            "initialized": True,
            "user_id": profile["user_id"],
            "initialized_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        INIT_STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _extract_field(self, content: str, field: str) -> str | None:
        match = re.search(rf"- \*\*{field}\*\*:\s*(.+?)(?:\n|$)", content)
        if not match:
            return None
        return match.group(1).strip()

    def _render_user_profile(self, profile: dict) -> str:
        habits = json.dumps(profile["habit_list"], ensure_ascii=False)
        return (
            "# USER.md - 用户配置\n\n"
            "## 基本信息\n"
            f"- **name**: {profile['name']}\n"
            f"- **timezone**: {profile['timezone']}\n\n"
            "## 播报设置\n"
            f"- **morning_broadcast**: {profile['morning_broadcast']}\n"
            f"- **evening_settlement**: {profile['evening_settlement']}\n"
            f"- **broadcast_channel**: {profile['broadcast_channel']}\n\n"
            "## 晨间签到设置\n"
            f"- **morning_target_time**: {profile['morning_target_time']}\n"
            f"- **early_bird_grace_minutes**: {profile['early_bird_grace_minutes']}\n\n"
            "## 风格设置\n"
            f"- **style**: {profile['style']}\n\n"
            "## 任务偏好\n"
            f"- **track_habits**: {str(profile['track_habits']).lower()}\n"
            f"- **habit_list**: {habits}\n"
        )
