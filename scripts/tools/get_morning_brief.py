"""Structured tool entrypoint for get_morning_brief."""

from scripts.core.settlement_service import SettlementService


def run(payload: dict) -> dict:
    return SettlementService().get_morning_brief(payload)
