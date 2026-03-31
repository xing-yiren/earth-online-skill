"""Structured tool entrypoint for init_skill_profile."""

from scripts.core.init_service import InitService


def run(payload: dict) -> dict:
    return InitService().init_skill_profile(payload)
