"""Structured tool entrypoint for apply_init_config."""

from scripts.core.init_service import InitService


def run(payload: dict) -> dict:
    return InitService().apply_init_config(payload)
