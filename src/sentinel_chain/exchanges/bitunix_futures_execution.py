"""Native Bitunix futures trading helpers for Sentinel Chain.

This module intentionally keeps live futures execution behind two gates:

1. ``AUTO_CRYPTO_BITUNIX_LIVE_ENABLED=true`` in the process environment.
2. ``confirm_live=LIVE_CONFIRMATION_PHRASE`` on every mutable API call.

Without both gates the methods return dry-run request previews that can be shown
in the UI, logged, unit-tested, or compared against Bitunix documentation without
placing an order.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from .bitunix_adapter import (
    BITUNIX_FUTURES_BASE_URL,
    BitunixConfigurationError,
    BitunixCredentials,
    BitunixRequestError,
    BitunixRestClient,
    bitunix_live_execution_enabled,
    load_bitunix_credentials_from_env,
)

LIVE_CONFIRMATION_PHRASE = "I_UNDERSTAND_THIS_PLACES_LIVE_FUTURES_ORDERS"


class BitunixLiveExecutionDisabled(PermissionError):
    """Raised when code attempts a live mutation without explicit operator gates."""


class BitunixFuturesValidationError(ValueError):
    """Raised when an order request cannot be mapped safely to Bitunix fields."""


@dataclass(frozen=True)
class BitunixMutationResult:
    """A live or dry-run result for a Bitunix mutable endpoint."""

    method: str
    endpoint: str
    body: dict[str, Any] = field(default_factory=dict)
    query: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = True
    live_enabled: bool = False
    submitted: bool = False
    response: dict[str, Any] | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["warnings"] = list(self.warnings)
        return data


def _plain(value: Any) -> str:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    return str(value)


def _optional_plain(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return _plain(value)


def _positive_decimal(value: Any, *, field_name: str) -> Decimal:
    if value is None or value == "":
        raise BitunixFuturesValidationError(f"{field_name} is required")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BitunixFuturesValidationError(f"{field_name} must be a decimal value") from exc
    if parsed <= 0:
        raise BitunixFuturesValidationError(f"{field_name} must be positive")
    return parsed


def _symbol_to_bitunix(symbol: str) -> str:
    normalized = str(symbol or "").strip().upper().replace("-", "/").replace("_", "/")
    if not normalized:
        raise BitunixFuturesValidationError("symbol is required")
    if "/" in normalized:
        base, quote = [part.strip() for part in normalized.split("/", 1)]
        if not base or not quote:
            raise BitunixFuturesValidationError(f"invalid symbol: {symbol}")
        return f"{base}{quote}"
    return normalized


def _normalize_choice(value: str, *, field_name: str, allowed: set[str]) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in allowed:
        raise BitunixFuturesValidationError(
            f"{field_name} must be one of {', '.join(sorted(allowed))}; got {value!r}"
        )
    return normalized


def _bitunix_side(side: str, *, reduce_only: bool, position_side: str | None = None) -> str:
    """Map Sentinel side into Bitunix side.

    For opening trades, Sentinel ``buy`` means long and ``sell`` means short.
    For reduce-only/close trades, Bitunix side is the side of the position being
    closed, not the trade direction. Therefore closing a long uses ``BUY`` and
    closing a short uses ``SELL``.
    """

    side_norm = str(side or "").strip().lower()
    position_norm = str(position_side or "").strip().lower()

    if reduce_only:
        if position_norm in {"long", "buy"}:
            return "BUY"
        if position_norm in {"short", "sell"}:
            return "SELL"
        if side_norm in {"sell", "close_long", "reduce_long", "sell_to_close"}:
            return "BUY"
        if side_norm in {"buy", "close_short", "buy_to_cover", "cover_short"}:
            return "SELL"
        raise BitunixFuturesValidationError(
            "reduce-only orders require side or position_side to identify the position direction"
        )

    if side_norm in {"buy", "long", "open_long", "buy_to_open"}:
        return "BUY"
    if side_norm in {"sell", "short", "open_short", "sell_short", "sell_to_open"}:
        return "SELL"
    raise BitunixFuturesValidationError(f"unsupported side: {side}")


def _trade_side(*, reduce_only: bool) -> str:
    return "CLOSE" if reduce_only else "OPEN"


def _clean_body(body: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in body.items() if value is not None and value != ""}


def _bool_from_env() -> bool:
    try:
        return bool(bitunix_live_execution_enabled())
    except Exception:
        return str(os.getenv("AUTO_CRYPTO_BITUNIX_LIVE_ENABLED", "")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }


class BitunixFuturesTradingClient(BitunixRestClient):
    """Bitunix USDT futures trading client with dry-run-first mutations."""

    def __init__(
        self,
        *,
        credentials: BitunixCredentials | None = None,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str = BITUNIX_FUTURES_BASE_URL,
        signing_style: str = "futures",
        nonce_factory: Any | None = None,
        clock_ms: Any | None = None,
        opener: Any | None = None,
    ) -> None:
        if credentials is None and (api_key is not None or secret_key is not None):
            credentials = BitunixCredentials(api_key=api_key or "", secret_key=secret_key or "")
        super().__init__(
            credentials=credentials,
            base_url=base_url,
            signing_style=signing_style,
            nonce_factory=nonce_factory,
            clock_ms=clock_ms,
            opener=opener,
        )

    def get_funding_rate(self, symbol: str) -> dict[str, Any]:
        return self.request_json(
            "GET",
            "/api/v1/futures/market/funding_rate",
            query={"symbol": _symbol_to_bitunix(symbol)},
            signed=False,
        )

    def get_pending_positions(self, symbol: str | None = None) -> dict[str, Any]:
        return super().get_pending_positions(_symbol_to_bitunix(symbol) if symbol else None)

    def get_pending_tp_sl_orders(
        self,
        *,
        symbol: str | None = None,
        position_id: str | None = None,
        side: str | None = None,
        position_mode: str | None = None,
        skip: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if symbol:
            query["symbol"] = _symbol_to_bitunix(symbol)
        if position_id:
            query["positionId"] = str(position_id)
        if side:
            query["side"] = _normalize_choice(side, field_name="side", allowed={"BUY", "SELL"})
        if position_mode:
            query["positionMode"] = _normalize_choice(
                position_mode,
                field_name="position_mode",
                allowed={"ONE_WAY", "HEDGE"},
            )
        if skip is not None:
            query["skip"] = int(skip)
        if limit is not None:
            query["limit"] = int(limit)
        return self.request_json("GET", "/api/v1/futures/tpsl/get_pending_orders", query=query, signed=True)

    def build_place_order_body(
        self,
        *,
        symbol: str,
        side: str,
        qty: Any,
        price: Any | None = None,
        reduce_only: bool = False,
        position_side: str | None = None,
        position_id: str | None = None,
        client_id: str | None = None,
        order_type: str | None = None,
        effect: str = "GTC",
        tp_price: Any | None = None,
        tp_stop_type: str = "MARK_PRICE",
        tp_order_type: str = "MARKET",
        tp_order_price: Any | None = None,
        sl_price: Any | None = None,
        sl_stop_type: str = "MARK_PRICE",
        sl_order_type: str = "MARKET",
        sl_order_price: Any | None = None,
    ) -> dict[str, Any]:
        qty_decimal = _positive_decimal(qty, field_name="qty")
        explicit_type = str(order_type).strip().upper() if order_type else None
        resolved_order_type = explicit_type or ("LIMIT" if price not in (None, "") else "MARKET")
        resolved_order_type = _normalize_choice(
            resolved_order_type,
            field_name="order_type",
            allowed={"LIMIT", "MARKET"},
        )
        resolved_effect = _normalize_choice(
            effect,
            field_name="effect",
            allowed={"GTC", "IOC", "FOK", "POST_ONLY"},
        )
        if resolved_order_type == "MARKET" and price not in (None, ""):
            raise BitunixFuturesValidationError("market orders cannot include price")
        if resolved_order_type == "LIMIT":
            _positive_decimal(price, field_name="price")

        body: dict[str, Any] = {
            "symbol": _symbol_to_bitunix(symbol),
            "qty": _plain(qty_decimal),
            "side": _bitunix_side(side, reduce_only=reduce_only, position_side=position_side),
            "tradeSide": _trade_side(reduce_only=reduce_only),
            "orderType": resolved_order_type,
            "effect": resolved_effect if resolved_order_type == "LIMIT" else None,
            "price": _optional_plain(price),
            "reduceOnly": bool(reduce_only),
            "positionId": str(position_id) if position_id else None,
            "clientId": str(client_id) if client_id else None,
            "tpPrice": _optional_plain(tp_price),
            "tpStopType": _normalize_choice(
                tp_stop_type,
                field_name="tp_stop_type",
                allowed={"MARK_PRICE", "LAST_PRICE"},
            )
            if tp_price not in (None, "")
            else None,
            "tpOrderType": _normalize_choice(
                tp_order_type,
                field_name="tp_order_type",
                allowed={"LIMIT", "MARKET"},
            )
            if tp_price not in (None, "")
            else None,
            "tpOrderPrice": _optional_plain(tp_order_price),
            "slPrice": _optional_plain(sl_price),
            "slStopType": _normalize_choice(
                sl_stop_type,
                field_name="sl_stop_type",
                allowed={"MARK_PRICE", "LAST_PRICE"},
            )
            if sl_price not in (None, "")
            else None,
            "slOrderType": _normalize_choice(
                sl_order_type,
                field_name="sl_order_type",
                allowed={"LIMIT", "MARKET"},
            )
            if sl_price not in (None, "")
            else None,
            "slOrderPrice": _optional_plain(sl_order_price),
        }
        return _clean_body(body)

    def place_order(self, *, dry_run: bool = True, confirm_live: str = "", **kwargs: Any) -> BitunixMutationResult:
        body = self.build_place_order_body(**kwargs)
        return self._mutate(
            "POST",
            "/api/v1/futures/trade/place_order",
            body=body,
            dry_run=dry_run,
            confirm_live=confirm_live,
        )

    def build_tp_sl_order_body(
        self,
        *,
        symbol: str,
        position_id: str,
        tp_price: Any | None = None,
        tp_qty: Any | None = None,
        tp_stop_type: str = "MARK_PRICE",
        tp_order_type: str = "MARKET",
        tp_order_price: Any | None = None,
        sl_price: Any | None = None,
        sl_qty: Any | None = None,
        sl_stop_type: str = "MARK_PRICE",
        sl_order_type: str = "MARKET",
        sl_order_price: Any | None = None,
    ) -> dict[str, Any]:
        if not position_id:
            raise BitunixFuturesValidationError("position_id is required for batch TP/SL orders")
        if tp_price in (None, "") and sl_price in (None, ""):
            raise BitunixFuturesValidationError("tp_price or sl_price is required")
        if tp_qty in (None, "") and sl_qty in (None, ""):
            raise BitunixFuturesValidationError("tp_qty or sl_qty is required")
        if tp_qty not in (None, ""):
            _positive_decimal(tp_qty, field_name="tp_qty")
        if sl_qty not in (None, ""):
            _positive_decimal(sl_qty, field_name="sl_qty")

        body: dict[str, Any] = {
            "symbol": _symbol_to_bitunix(symbol),
            "positionId": str(position_id),
            "tpPrice": _optional_plain(tp_price),
            "tpQty": _optional_plain(tp_qty),
            "tpStopType": _normalize_choice(
                tp_stop_type,
                field_name="tp_stop_type",
                allowed={"MARK_PRICE", "LAST_PRICE"},
            )
            if tp_price not in (None, "")
            else None,
            "tpOrderType": _normalize_choice(
                tp_order_type,
                field_name="tp_order_type",
                allowed={"LIMIT", "MARKET"},
            )
            if tp_price not in (None, "")
            else None,
            "tpOrderPrice": _optional_plain(tp_order_price),
            "slPrice": _optional_plain(sl_price),
            "slQty": _optional_plain(sl_qty),
            "slStopType": _normalize_choice(
                sl_stop_type,
                field_name="sl_stop_type",
                allowed={"MARK_PRICE", "LAST_PRICE"},
            )
            if sl_price not in (None, "")
            else None,
            "slOrderType": _normalize_choice(
                sl_order_type,
                field_name="sl_order_type",
                allowed={"LIMIT", "MARKET"},
            )
            if sl_price not in (None, "")
            else None,
            "slOrderPrice": _optional_plain(sl_order_price),
        }
        return _clean_body(body)

    def place_tp_sl_order(self, *, dry_run: bool = True, confirm_live: str = "", **kwargs: Any) -> BitunixMutationResult:
        body = self.build_tp_sl_order_body(**kwargs)
        return self._mutate(
            "POST",
            "/api/v1/futures/tpsl/place_order",
            body=body,
            dry_run=dry_run,
            confirm_live=confirm_live,
        )

    def build_position_tp_sl_order_body(
        self,
        *,
        symbol: str,
        position_id: str,
        tp_price: Any | None = None,
        tp_stop_type: str = "MARK_PRICE",
        sl_price: Any | None = None,
        sl_stop_type: str = "MARK_PRICE",
    ) -> dict[str, Any]:
        if not position_id:
            raise BitunixFuturesValidationError("position_id is required for position TP/SL orders")
        if tp_price in (None, "") and sl_price in (None, ""):
            raise BitunixFuturesValidationError("tp_price or sl_price is required")
        body: dict[str, Any] = {
            "symbol": _symbol_to_bitunix(symbol),
            "positionId": str(position_id),
            "tpPrice": _optional_plain(tp_price),
            "tpStopType": _normalize_choice(
                tp_stop_type,
                field_name="tp_stop_type",
                allowed={"MARK_PRICE", "LAST_PRICE"},
            )
            if tp_price not in (None, "")
            else None,
            "slPrice": _optional_plain(sl_price),
            "slStopType": _normalize_choice(
                sl_stop_type,
                field_name="sl_stop_type",
                allowed={"MARK_PRICE", "LAST_PRICE"},
            )
            if sl_price not in (None, "")
            else None,
        }
        return _clean_body(body)

    def place_position_tp_sl_order(
        self,
        *,
        dry_run: bool = True,
        confirm_live: str = "",
        **kwargs: Any,
    ) -> BitunixMutationResult:
        body = self.build_position_tp_sl_order_body(**kwargs)
        return self._mutate(
            "POST",
            "/api/v1/futures/tpsl/position/place_order",
            body=body,
            dry_run=dry_run,
            confirm_live=confirm_live,
        )

    def change_leverage(
        self,
        *,
        margin_coin: str,
        symbol: str,
        leverage: Any,
        dry_run: bool = True,
        confirm_live: str = "",
    ) -> BitunixMutationResult:
        leverage_decimal = _positive_decimal(leverage, field_name="leverage")
        body = {
            "marginCoin": str(margin_coin or "USDT").upper(),
            "symbol": _symbol_to_bitunix(symbol),
            "leverage": _plain(leverage_decimal),
        }
        return self._mutate(
            "POST",
            "/api/v1/futures/account/change_leverage",
            body=body,
            dry_run=dry_run,
            confirm_live=confirm_live,
        )

    def change_margin_mode(
        self,
        *,
        margin_coin: str,
        symbol: str,
        margin_mode: str,
        dry_run: bool = True,
        confirm_live: str = "",
    ) -> BitunixMutationResult:
        body = {
            "marginCoin": str(margin_coin or "USDT").upper(),
            "symbol": _symbol_to_bitunix(symbol),
            "marginMode": _normalize_choice(
                margin_mode,
                field_name="margin_mode",
                allowed={"ISOLATION", "CROSS"},
            ),
        }
        return self._mutate(
            "POST",
            "/api/v1/futures/account/change_margin_mode",
            body=body,
            dry_run=dry_run,
            confirm_live=confirm_live,
        )

    def _mutate(
        self,
        method: str,
        endpoint: str,
        *,
        body: dict[str, Any],
        query: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirm_live: str = "",
    ) -> BitunixMutationResult:
        live_enabled = _bool_from_env()
        warnings: list[str] = []
        if dry_run:
            warnings.append("dry_run=true; request was not submitted")
            return BitunixMutationResult(
                method=method,
                endpoint=endpoint,
                body=body,
                query=query or {},
                dry_run=True,
                live_enabled=live_enabled,
                submitted=False,
                warnings=tuple(warnings),
            )
        if not live_enabled:
            raise BitunixLiveExecutionDisabled(
                "Set AUTO_CRYPTO_BITUNIX_LIVE_ENABLED=true before submitting mutable Bitunix futures requests."
            )
        if confirm_live != LIVE_CONFIRMATION_PHRASE:
            raise BitunixLiveExecutionDisabled(
                "confirm_live must match LIVE_CONFIRMATION_PHRASE before submitting live Bitunix futures requests."
            )
        try:
            response = self.request_json(method, endpoint, query=query or {}, body=body, signed=True)
        except BitunixRequestError:
            raise
        return BitunixMutationResult(
            method=method,
            endpoint=endpoint,
            body=body,
            query=query or {},
            dry_run=False,
            live_enabled=live_enabled,
            submitted=True,
            response=response,
            warnings=tuple(warnings),
        )


def load_bitunix_futures_trading_client_from_env() -> BitunixFuturesTradingClient:
    credentials = load_bitunix_credentials_from_env()
    if credentials is None or not credentials.configured:
        raise BitunixConfigurationError("Bitunix API key and secret are required")
    return BitunixFuturesTradingClient(
        credentials=credentials,
        base_url=os.getenv("AUTO_CRYPTO_BITUNIX_BASE_URL", BITUNIX_FUTURES_BASE_URL),
    )
