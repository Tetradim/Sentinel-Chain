from __future__ import annotations

from .signals import CryptoSignal


class ApprovalQueue:
    """In-memory pending signal queue for human approval workflows."""

    def __init__(self) -> None:
        self._pending: dict[str, CryptoSignal] = {}

    def add(self, signal: CryptoSignal) -> None:
        self._pending[signal.signal_id] = signal

    def pop(self, signal_id: str) -> CryptoSignal | None:
        return self._pending.pop(signal_id, None)

    def list_pending(self) -> list[dict]:
        return [_summary(signal) for signal in self._pending.values()]


def _summary(signal: CryptoSignal) -> dict:
    return {
        "signal_id": signal.signal_id,
        "symbol": signal.symbol,
        "side": signal.side,
        "exchange": signal.exchange,
        "quote_amount": str(signal.quote_amount) if signal.quote_amount is not None else None,
        "base_amount": str(signal.base_amount) if signal.base_amount is not None else None,
        "price": str(signal.price) if signal.price is not None else None,
        "strategy_id": signal.strategy_id,
    }

