from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from ..config import live_execution_enabled_from_env
from .platform_registry import get_platform


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
    attached_stop_loss_take_profit: bool = False
    oco_order: bool = False
    trailing_order: bool = False
    reduce_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "exchange_id": self.exchange_id,
            "spot": self.spot,
            "margin": self.margin,
            "swap": self.swap,
            "future": self.future,
            "option": self.option,
            "create_order": self.create_order,
            "cancel_order": self.cancel_order,
            "fetch_balance": self.fetch_balance,
            "attached_stop_loss_take_profit": self.attached_stop_loss_take_profit,
            "oco_order": self.oco_order,
            "trailing_order": self.trailing_order,
            "reduce_only": self.reduce_only,
        }


class CcxtExchangeAdapter:
    """Thin CCXT wrapper for future live exchange support.

    The MVP keeps live trading out of the default path. This adapter exists so
    venue integrations can be added behind the same capability boundary without
    changing signal, risk, or Discord code.
    """

    def __init__(self, exchange_id: str, credentials: dict[str, Any] | None = None) -> None:
        ccxt = _load_ccxt()
        exchange_id = normalize_ccxt_exchange_id(exchange_id)

        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"unsupported ccxt exchange: {exchange_id}")

        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(credentials or {})
        self.exchange_id = exchange_id

    def capabilities(self) -> ExchangeCapabilities:
        has = self.exchange.has or {}
        return ExchangeCapabilities(
            exchange_id=self.exchange_id,
            spot=bool(has.get("spot")),
            margin=bool(has.get("margin")),
            swap=bool(has.get("swap")),
            future=bool(has.get("future")),
            option=bool(has.get("option")),
            create_order=bool(has.get("createOrder")),
            cancel_order=bool(has.get("cancelOrder")),
            fetch_balance=bool(has.get("fetchBalance")),
            attached_stop_loss_take_profit=_truthy_has(
                has,
                "createOrderWithTakeProfitAndStopLoss",
                "createOrderWithStopLossAndTakeProfit",
                "attachedStopLossTakeProfit",
            ),
            oco_order=_truthy_has(has, "createOcoOrder", "createOCOOrder", "ocoOrder"),
            trailing_order=_truthy_has(has, "createTrailingOrder", "trailingOrder", "trailingStop"),
            reduce_only=_truthy_has(has, "reduceOnly", "createReduceOnlyOrder"),
        )

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return self.exchange.fetch_ticker(symbol)

    def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, Any]:
        if symbols:
            return self.exchange.fetch_tickers(symbols)
        return self.exchange.fetch_tickers()

    def fetch_balance(self) -> dict[str, Any]:
        return self.exchange.fetch_balance()

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: Any,
        price: Any = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.exchange.create_order(symbol, order_type, side, amount, price, params or {})

    def cancel_order(self, order_id: str, symbol: str | None = None, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.exchange.cancel_order(order_id, symbol, params or {})


def list_ccxt_exchange_ids() -> list[str]:
    ccxt = _load_ccxt()
    return sorted(str(exchange_id) for exchange_id in getattr(ccxt, "exchanges", []))


def normalize_ccxt_exchange_id(exchange_id: str) -> str:
    normalized = str(exchange_id or "").strip().lower()
    platform = get_platform(normalized)
    if platform and platform.ccxt_id:
        return platform.ccxt_id
    return normalized


def ccxt_env_prefix(exchange_id: str) -> str:
    normalized = normalize_ccxt_exchange_id(exchange_id)
    return re.sub(r"[^A-Z0-9]", "", normalized.upper())


def ccxt_live_enabled_env(exchange_id: str) -> str:
    return f"AUTO_CRYPTO_{ccxt_env_prefix(exchange_id)}_LIVE_ENABLED"


def ccxt_live_execution_enabled(exchange_id: str) -> bool:
    platform = get_platform(str(exchange_id or ""))
    if platform and platform.live_enabled_env:
        return platform.live_execution_enabled()
    return live_execution_enabled_from_env(ccxt_live_enabled_env(exchange_id))


def ccxt_credentials_from_env(exchange_id: str) -> dict[str, Any]:
    prefix = ccxt_env_prefix(exchange_id)
    candidates: dict[str, tuple[str, ...]] = {
        "apiKey": (f"AUTO_CRYPTO_{prefix}_API_KEY", f"AUTO_CRYPTO_{prefix}_KEY"),
        "secret": (f"AUTO_CRYPTO_{prefix}_API_SECRET", f"AUTO_CRYPTO_{prefix}_SECRET_KEY", f"AUTO_CRYPTO_{prefix}_SECRET"),
        "password": (f"AUTO_CRYPTO_{prefix}_PASSPHRASE", f"AUTO_CRYPTO_{prefix}_PASSWORD"),
        "uid": (f"AUTO_CRYPTO_{prefix}_UID", f"AUTO_CRYPTO_{prefix}_ACCOUNT_ID"),
    }
    credentials: dict[str, Any] = {"enableRateLimit": True}
    for ccxt_key, env_names in candidates.items():
        for env_name in env_names:
            value = os.getenv(env_name)
            if value and value.strip():
                credentials[ccxt_key] = value.strip()
                break
    return credentials


def ccxt_credentials_status(exchange_id: str) -> dict[str, Any]:
    normalized = normalize_ccxt_exchange_id(exchange_id)
    prefix = ccxt_env_prefix(normalized)
    credentials = ccxt_credentials_from_env(normalized)
    configured_fields = sorted(key for key in credentials if key != "enableRateLimit")
    platform = get_platform(str(exchange_id or ""))
    platform_configured = platform.credentials_configured() if platform else False
    return {
        "exchange_id": normalized,
        "env_prefix": f"AUTO_CRYPTO_{prefix}_",
        "configured": platform_configured or ("apiKey" in credentials and "secret" in credentials),
        "ccxt_configured": "apiKey" in credentials and "secret" in credentials,
        "platform_configured": platform_configured,
        "configured_fields": configured_fields,
        "live_enabled_env": platform.live_enabled_env if platform and platform.live_enabled_env else ccxt_live_enabled_env(normalized),
        "live_execution_enabled": ccxt_live_execution_enabled(normalized),
    }


def _load_ccxt() -> Any:
    try:
        import ccxt  # type: ignore
    except ImportError as exc:
        raise CcxtNotInstalledError("Install sentinel-chain[exchange] to enable CCXT adapters") from exc
    return ccxt


def _truthy_has(has: dict[str, Any], *names: str) -> bool:
    return any(bool(has.get(name)) for name in names)
