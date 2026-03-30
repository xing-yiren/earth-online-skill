"""Structured tool entrypoint for get_daily_settlement."""

from scripts.core.settlement_service import SettlementService


def run(payload: dict) -> dict:
    return SettlementService().get_daily_settlement(payload)
