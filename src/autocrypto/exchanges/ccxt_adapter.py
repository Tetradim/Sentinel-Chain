from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CcxtNotInstalledError(RuntimeError):
    """Raised when the optional ccxt dependency is needed but unavailable."""


@dataclass(frozen=True)
class ExchangeCapabilities:
    exchange_id: str
    spot: bool
    margin: bool
    swap: bool
    future: bool
    option: bool
    create_order: bool
    cancel_order: bool
    fetch_balance: bool


class CcxtExchangeAdapter:
    """Thin CCXT wrapper for future live exchange support.

    The MVP keeps live trading out of the default path. This adapter exists so
    venue integrations can be added behind the same capability boundary without
    changing signal, risk, or Discord code.
    """

    def __init__(self, exchange_id: str, credentials: dict[str, Any] | None = None) -> None:
        try:
            import ccxt  # type: ignore
        except ImportError as exc:
            raise CcxtNotInstalledError("Install auto-crypto[exchange] to enable CCXT adapters") from exc

        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"unsupported ccxt exchange: {exchange_id}")

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(credentials or {})
        self.exchange_id = exchange_id

    def capabilities(self) -> ExchangeCapabilities:
        has = self.exchange.has or {}
        return ExchangeCapabilities(
            exchange_id=self.exchange_id,
            spot=True,
            margin=bool(has.get("margin")),
            swap=bool(has.get("swap")),
            future=bool(has.get("future")),
            option=bool(has.get("option")),
            create_order=bool(has.get("createOrder")),
            cancel_order=bool(has.get("cancelOrder")),
            fetch_balance=bool(has.get("fetchBalance")),
        )

