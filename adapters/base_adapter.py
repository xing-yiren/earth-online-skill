"""Base adapter contract for claw-style host platforms."""

from __future__ import annotations


class BaseHostAdapter:
    """Abstract interface for converting host state into host_context."""

    platform_name = "unknown"

    def get_platform_info(self) -> dict:
        raise NotImplementedError

    def get_user_info(self) -> dict:
        raise NotImplementedError

    def get_session_info(self) -> dict:
        raise NotImplementedError

    def get_intent_info(self, raw_input: str | None = None) -> dict:
        raise NotImplementedError

    def get_context_info(self) -> dict:
        raise NotImplementedError

    def get_runtime_info(self) -> dict:
        return {}

    def build_host_context(self, raw_input: str | None = None) -> dict:
        return {
            "host": self.get_platform_info(),
            "user": self.get_user_info(),
            "session": self.get_session_info(),
            "intent": self.get_intent_info(raw_input),
            "context": self.get_context_info(),
            "runtime": self.get_runtime_info(),
        }
