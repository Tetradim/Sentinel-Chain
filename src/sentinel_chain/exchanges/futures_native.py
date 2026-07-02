"""Venue-aware futures bracket planning for Sentinel Chain.

The existing Sentinel Chain planner intentionally avoids live execution. This
module keeps that safety stance while giving the UI and operator a much richer
venue-specific plan: native Bitunix request bodies where the public REST API is
clear, CCXT parameter hints where CCXT exposes portable features, and explicit
paper/synthetic warnings for features that cannot be made portable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from sentinel_chain.signals import CryptoSignal, TakeProfitTarget

try:  # Optional in older checkouts; keep the planner importable.
    from sentinel_chain.futures_risk import FuturesRiskConfig, FuturesTradeContext, assess_futures_trade
except Exception:  # pragma: no cover - only used when installed against older repo snapshots.
    FuturesRiskConfig = None  # type: ignore[assignment]
    FuturesTradeContext = None  # type: ignore[assignment]
    assess_futures_trade = None  # type: ignore[assignment]

from .bitunix_futures_execution import BitunixFuturesTradingClient, LIVE_CONFIRMATION_PHRASE


@dataclass(frozen=True)
class FuturesSizingResult:
    qty: Decimal | None
    notional: Decimal | None
    margin_required: Decimal | None
    entry_price: Decimal | None
    source: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "qty": _decimal_or_none(self.qty),
            "notional": _decimal_or_none(self.notional),
            "margin_required": _decimal_or_none(self.margin_required),
            "entry_price": _decimal_or_none(self.entry_price),
            "source": self.source,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class NativeFuturesLeg:
    id: str
    role: str
    venue: str
    method: str | None = None
    endpoint: str | None = None
    body: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    submit_after: str | None = None
    native: bool = True
    reduce_only: bool = False
    requires_position_id: bool = False
    paper_managed: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["notes"] = list(self.notes)
        return data


@dataclass(frozen=True)
class NativeFuturesPlan:
    plan_id: str
    venue: str
    symbol: str
    market_type: str
    side: str
    strategy: str
    live_confirmation_phrase: str
    sizing: FuturesSizingResult
    legs: tuple[NativeFuturesLeg, ...]
    risk: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    unsupported_features: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "venue": self.venue,
            "symbol": self.symbol,
            "market_type": self.market_type,
            "side": self.side,
            "strategy": self.strategy,
            "live_confirmation_phrase": self.live_confirmation_phrase,
            "sizing": self.sizing.to_dict(),
            "legs": [leg.to_dict() for leg in self.legs],
            "risk": self.risk,
            "warnings": list(self.warnings),
            "unsupported_features": list(self.unsupported_features),
        }


def build_native_futures_plan(
    signal: CryptoSignal,
    *,
    venue: str | None = None,
    mark_price: Any | None = None,
    equity: Any | None = None,
    position_id: str | None = None,
    margin_mode: str = "ISOLATION",
    margin_coin: str = "USDT",
    trigger_price_type: str = "MARK_PRICE",
    order_effect: str = "GTC",
    ccxt_capabilities: Mapping[str, Any] | None = None,
) -> NativeFuturesPlan:
    """Build a non-executing native futures bracket plan."""

    resolved_venue = (venue or signal.exchange or "paper").strip().lower()
    sizing = _sizing_for(signal, mark_price=mark_price, equity=equity)
    stop_price = _stop_loss_price(signal, sizing.entry_price)
    targets = _targets_with_prices(signal, sizing.entry_price)
    warnings: list[str] = list(sizing.warnings)
    unsupported: list[str] = []
    risk = _risk_assessment(signal, mark_price=mark_price, equity=equity, stop_price=stop_price)

    if resolved_venue in {"bitunix", "bitunix_futures", "bitunix-usdt"}:
        return _bitunix_plan(
            signal,
            venue="bitunix",
            sizing=sizing,
            stop_price=stop_price,
            targets=targets,
            position_id=position_id,
            margin_mode=margin_mode,
            margin_coin=margin_coin,
            trigger_price_type=trigger_price_type,
            order_effect=order_effect,
            inherited_warnings=warnings,
            inherited_unsupported=unsupported,
            risk=risk,
        )

    return _ccxt_or_paper_plan(
        signal,
        venue=resolved_venue,
        sizing=sizing,
        stop_price=stop_price,
        targets=targets,
        ccxt_capabilities=ccxt_capabilities or {},
        trigger_price_type=trigger_price_type,
        inherited_warnings=warnings,
        inherited_unsupported=unsupported,
        risk=risk,
    )


def dry_run_bitunix_requests(plan: NativeFuturesPlan) -> list[dict[str, Any]]:
    """Convert executable Bitunix legs in a plan to dry-run mutation previews."""

    client = BitunixFuturesTradingClient(api_key="DRY_RUN", secret_key="DRY_RUN")
    results: list[dict[str, Any]] = []
    for leg in plan.legs:
        if leg.venue != "bitunix" or not leg.endpoint or leg.method != "POST" or leg.paper_managed:
            continue
        endpoint = leg.endpoint
        if endpoint.endswith("/trade/place_order"):
            results.append(
                client._mutate("POST", endpoint, body=leg.body, dry_run=True).to_dict()  # noqa: SLF001
            )
        elif endpoint.endswith("/tpsl/place_order"):
            results.append(
                client._mutate("POST", endpoint, body=leg.body, dry_run=True).to_dict()  # noqa: SLF001
            )
        elif endpoint.endswith("/tpsl/position/place_order"):
            results.append(
                client._mutate("POST", endpoint, body=leg.body, dry_run=True).to_dict()  # noqa: SLF001
            )
        elif endpoint.endswith("/account/change_leverage") or endpoint.endswith("/account/change_margin_mode"):
            results.append(
                client._mutate("POST", endpoint, body=leg.body, dry_run=True).to_dict()  # noqa: SLF001
            )
    return results


def _bitunix_plan(
    signal: CryptoSignal,
    *,
    venue: str,
    sizing: FuturesSizingResult,
    stop_price: Decimal | None,
    targets: tuple[TakeProfitTarget, ...],
    position_id: str | None,
    margin_mode: str,
    margin_coin: str,
    trigger_price_type: str,
    order_effect: str,
    inherited_warnings: list[str],
    inherited_unsupported: list[str],
    risk: dict[str, Any],
) -> NativeFuturesPlan:
    warnings = list(inherited_warnings)
    unsupported = list(inherited_unsupported)
    legs: list[NativeFuturesLeg] = []
    client = BitunixFuturesTradingClient(api_key="DRY_RUN", secret_key="DRY_RUN")

    if sizing.qty is None:
        warnings.append("quantity could not be derived; entry and exit legs are placeholders only")
        qty_for_preview: Decimal = Decimal("0")
    else:
        qty_for_preview = sizing.qty

    # Account setup legs are explicit in the plan so the UI can show what the
    # operator must configure. They remain optional and live-gated.
    if signal.leverage and _decimal(signal.leverage) != Decimal("1"):
        legs.append(
            NativeFuturesLeg(
                id="account-leverage",
                role="set_leverage",
                venue=venue,
                method="POST",
                endpoint="/api/v1/futures/account/change_leverage",
                body={
                    "marginCoin": margin_coin.upper(),
                    "symbol": _exchange_symbol(signal.symbol),
                    "leverage": _decimal_to_str(signal.leverage),
                },
                native=True,
                notes=("Must be submitted before opening the position.",),
            )
        )
    if margin_mode:
        legs.append(
            NativeFuturesLeg(
                id="account-margin-mode",
                role="set_margin_mode",
                venue=venue,
                method="POST",
                endpoint="/api/v1/futures/account/change_margin_mode",
                body={
                    "marginCoin": margin_coin.upper(),
                    "symbol": _exchange_symbol(signal.symbol),
                    "marginMode": str(margin_mode).upper(),
                },
                native=True,
                notes=("Bitunix may reject margin-mode changes while positions or open orders exist.",),
            )
        )

    simple = _simple_full_bitunix_bracket(signal, targets)
    entry_body: dict[str, Any] | None = None
    if qty_for_preview > 0:
        first_target = targets[0] if targets else None
        if simple:
            entry_body = client.build_place_order_body(
                symbol=signal.symbol,
                side=signal.side,
                qty=qty_for_preview,
                price=signal.price,
                reduce_only=signal.reduce_only,
                order_type="LIMIT" if signal.price else "MARKET",
                effect=order_effect,
                tp_price=first_target.trigger_price if first_target else None,
                tp_stop_type=trigger_price_type,
                sl_price=stop_price,
                sl_stop_type=trigger_price_type,
            )
        else:
            entry_body = client.build_place_order_body(
                symbol=signal.symbol,
                side=signal.side,
                qty=qty_for_preview,
                price=signal.price,
                reduce_only=signal.reduce_only,
                order_type="LIMIT" if signal.price else "MARKET",
                effect=order_effect,
            )
    else:
        entry_body = {
            "symbol": _exchange_symbol(signal.symbol),
            "side": "BUY" if signal.side == "buy" else "SELL",
            "tradeSide": "CLOSE" if signal.reduce_only else "OPEN",
            "qty": "<derive-qty>",
            "orderType": "LIMIT" if signal.price else "MARKET",
        }

    legs.append(
        NativeFuturesLeg(
            id="entry",
            role="entry",
            venue=venue,
            method="POST",
            endpoint="/api/v1/futures/trade/place_order",
            body=entry_body,
            native=True,
            reduce_only=signal.reduce_only,
            notes=(
                "Simple one-target brackets can attach TP/SL to the Bitunix entry request."
                if simple
                else "Entry is separate because the requested bracket needs position-aware or synthetic management."
            ),
        )
    )

    if simple:
        strategy = "bitunix_attached_tpsl_on_entry"
    else:
        strategy = "bitunix_entry_then_position_or_batch_tpsl"
        if signal.trailing_stop_pct or signal.trailing_stop_amount or signal.trailing_stop_price:
            unsupported.append(
                "Bitunix UI documents trailing stops, but this add-on only uses official REST fields that were explicit in the reviewed place-order and TP/SL pages; trailing remains paper/synthetic unless a confirmed REST trailing endpoint is added."
            )
            legs.append(
                NativeFuturesLeg(
                    id="synthetic-trailing-stop",
                    role="trailing_stop",
                    venue=venue,
                    native=False,
                    paper_managed=True,
                    reduce_only=True,
                    notes=(
                        "Manage as a Sentinel synthetic trailing stop or route through a venue/CCXT adapter that advertises native trailing support.",
                    ),
                )
            )
        if signal.breakeven_after_take_profit or signal.breakeven_trigger_pct:
            legs.append(
                NativeFuturesLeg(
                    id="synthetic-breakeven",
                    role="breakeven_stop_move",
                    venue=venue,
                    native=False,
                    paper_managed=True,
                    reduce_only=True,
                    notes=("Move the stop to breakeven after trigger/fill in the Sentinel bracket manager.",),
                )
            )
        if signal.max_hold_marks:
            legs.append(
                NativeFuturesLeg(
                    id="synthetic-time-stop",
                    role="time_stop",
                    venue=venue,
                    native=False,
                    paper_managed=True,
                    reduce_only=True,
                    notes=("Close or alert after max_hold_marks in the Sentinel bracket manager.",),
                )
            )

        if targets or stop_price:
            if position_id:
                for index, target in enumerate(targets, start=1):
                    close_qty = _close_qty(qty_for_preview, target.close_pct)
                    if close_qty is None:
                        continue
                    body = client.build_tp_sl_order_body(
                        symbol=signal.symbol,
                        position_id=position_id,
                        tp_price=target.trigger_price,
                        tp_qty=close_qty,
                        tp_stop_type=trigger_price_type,
                    )
                    legs.append(
                        NativeFuturesLeg(
                            id=f"take-profit-{index}",
                            role="take_profit",
                            venue=venue,
                            method="POST",
                            endpoint="/api/v1/futures/tpsl/place_order",
                            body=body,
                            submit_after="entry_fill",
                            native=True,
                            reduce_only=True,
                        )
                    )
                if stop_price:
                    body = client.build_position_tp_sl_order_body(
                        symbol=signal.symbol,
                        position_id=position_id,
                        sl_price=stop_price,
                        sl_stop_type=trigger_price_type,
                    )
                    legs.append(
                        NativeFuturesLeg(
                            id="position-stop-loss",
                            role="stop_loss",
                            venue=venue,
                            method="POST",
                            endpoint="/api/v1/futures/tpsl/position/place_order",
                            body=body,
                            submit_after="entry_fill",
                            native=True,
                            reduce_only=True,
                            notes=("Whole-position stop; batch TP orders can coexist, but the exchange may cancel paired exits after one side triggers.",),
                        )
                    )
            else:
                legs.append(
                    NativeFuturesLeg(
                        id="await-position-id",
                        role="position_lookup",
                        venue=venue,
                        submit_after="entry_fill",
                        native=True,
                        requires_position_id=True,
                        notes=(
                            "After entry fill, query pending positions to obtain Bitunix positionId, then submit batch/position TP/SL legs.",
                        ),
                    )
                )

    return NativeFuturesPlan(
        plan_id=f"{signal.signal_id}:futures:{venue}",
        venue=venue,
        symbol=signal.symbol,
        market_type=signal.market_type,
        side=signal.side,
        strategy=strategy,
        live_confirmation_phrase=LIVE_CONFIRMATION_PHRASE,
        sizing=sizing,
        legs=tuple(legs),
        risk=risk,
        warnings=tuple(warnings),
        unsupported_features=tuple(unsupported),
    )


def _ccxt_or_paper_plan(
    signal: CryptoSignal,
    *,
    venue: str,
    sizing: FuturesSizingResult,
    stop_price: Decimal | None,
    targets: tuple[TakeProfitTarget, ...],
    ccxt_capabilities: Mapping[str, Any],
    trigger_price_type: str,
    inherited_warnings: list[str],
    inherited_unsupported: list[str],
    risk: dict[str, Any],
) -> NativeFuturesPlan:
    warnings = list(inherited_warnings)
    unsupported = list(inherited_unsupported)
    legs: list[NativeFuturesLeg] = []
    qty_text = _decimal_or_none(sizing.qty) or "<derive-qty>"
    entry_type = "limit" if signal.price else "market"
    amount = qty_text
    params: dict[str, Any] = {}

    attached_supported = bool(ccxt_capabilities.get("attachedStopLossTakeProfit"))
    trailing_supported = bool(ccxt_capabilities.get("trailing"))
    reduce_only_supported = ccxt_capabilities.get("reduceOnly", True)

    if attached_supported and len(targets) <= 1 and stop_price:
        if targets:
            params["takeProfit"] = {"triggerPrice": _decimal_or_none(targets[0].trigger_price)}
        params["stopLoss"] = {"triggerPrice": _decimal_or_none(stop_price)}
        strategy = "ccxt_attached_tpsl"
    else:
        strategy = "ccxt_independent_reduce_only_or_paper_bracket"

    legs.append(
        NativeFuturesLeg(
            id="entry",
            role="entry",
            venue=venue,
            params={
                "method": "create_order",
                "symbol": signal.symbol,
                "type": entry_type,
                "side": signal.side,
                "amount": amount,
                "price": _decimal_or_none(signal.price),
                "params": params,
            },
            native=True,
            notes=("CCXT futures amount may be contract count; check market['contractSize'] before live use.",),
        )
    )

    if not attached_supported:
        for index, target in enumerate(targets, start=1):
            close_qty = _close_qty(sizing.qty, target.close_pct)
            legs.append(
                NativeFuturesLeg(
                    id=f"take-profit-{index}",
                    role="take_profit",
                    venue=venue,
                    params={
                        "method": "create_order",
                        "symbol": signal.symbol,
                        "type": "market",
                        "side": _opposite_side(signal.side),
                        "amount": _decimal_or_none(close_qty) or "<derive-close-qty>",
                        "price": None,
                        "params": {
                            "takeProfitPrice": _decimal_or_none(target.trigger_price),
                            "triggerPrice": _decimal_or_none(target.trigger_price),
                            "reduceOnly": bool(reduce_only_supported),
                            "triggerPriceType": trigger_price_type,
                        },
                    },
                    native=True,
                    reduce_only=True,
                    submit_after="entry_fill",
                )
            )
        if stop_price:
            legs.append(
                NativeFuturesLeg(
                    id="stop-loss",
                    role="stop_loss",
                    venue=venue,
                    params={
                        "method": "create_order",
                        "symbol": signal.symbol,
                        "type": "market",
                        "side": _opposite_side(signal.side),
                        "amount": amount,
                        "price": None,
                        "params": {
                            "stopLossPrice": _decimal_or_none(stop_price),
                            "triggerPrice": _decimal_or_none(stop_price),
                            "reduceOnly": bool(reduce_only_supported),
                            "triggerPriceType": trigger_price_type,
                        },
                    },
                    native=True,
                    reduce_only=True,
                    submit_after="entry_fill",
                )
            )

    if signal.trailing_stop_pct or signal.trailing_stop_amount or signal.trailing_activation_price:
        if trailing_supported:
            trail_params: dict[str, Any] = {"reduceOnly": True}
            if signal.trailing_stop_pct:
                trail_params["trailingPercent"] = _decimal_or_none(signal.trailing_stop_pct)
            if signal.trailing_stop_amount:
                trail_params["trailingAmount"] = _decimal_or_none(signal.trailing_stop_amount)
            if signal.trailing_activation_price:
                trail_params["trailingTriggerPrice"] = _decimal_or_none(signal.trailing_activation_price)
            legs.append(
                NativeFuturesLeg(
                    id="trailing-stop",
                    role="trailing_stop",
                    venue=venue,
                    params={
                        "method": "create_order",
                        "symbol": signal.symbol,
                        "type": "market",
                        "side": _opposite_side(signal.side),
                        "amount": _decimal_or_none(_close_qty(sizing.qty, signal.trailing_stop_close_pct)) or amount,
                        "price": None,
                        "params": trail_params,
                    },
                    native=True,
                    reduce_only=True,
                    submit_after="entry_fill",
                )
            )
            strategy += "+ccxt_trailing"
        else:
            unsupported.append("venue capabilities do not advertise CCXT trailing orders; manage trailing synthetically")
            legs.append(
                NativeFuturesLeg(
                    id="synthetic-trailing-stop",
                    role="trailing_stop",
                    venue=venue,
                    native=False,
                    paper_managed=True,
                    reduce_only=True,
                )
            )

    if signal.breakeven_after_take_profit or signal.breakeven_trigger_pct:
        legs.append(
            NativeFuturesLeg(
                id="synthetic-breakeven",
                role="breakeven_stop_move",
                venue=venue,
                native=False,
                paper_managed=True,
                reduce_only=True,
            )
        )
    if signal.max_hold_marks:
        legs.append(
            NativeFuturesLeg(
                id="synthetic-time-stop",
                role="time_stop",
                venue=venue,
                native=False,
                paper_managed=True,
                reduce_only=True,
            )
        )

    if not targets and not stop_price and not (signal.trailing_stop_pct or signal.trailing_stop_amount):
        warnings.append("no protective bracket exits were configured")

    return NativeFuturesPlan(
        plan_id=f"{signal.signal_id}:futures:{venue}",
        venue=venue,
        symbol=signal.symbol,
        market_type=signal.market_type,
        side=signal.side,
        strategy=strategy,
        live_confirmation_phrase=LIVE_CONFIRMATION_PHRASE,
        sizing=sizing,
        legs=tuple(legs),
        risk=risk,
        warnings=tuple(warnings),
        unsupported_features=tuple(unsupported),
    )


def _sizing_for(signal: CryptoSignal, *, mark_price: Any | None, equity: Any | None) -> FuturesSizingResult:
    entry = _decimal(signal.price) or _decimal(mark_price)
    leverage = _decimal(signal.leverage) or Decimal("1")
    warnings: list[str] = []
    qty: Decimal | None = None
    notional: Decimal | None = None
    source = "unresolved"

    if signal.base_amount:
        qty = _decimal(signal.base_amount)
        source = "base_amount"
    elif signal.quote_amount and entry:
        qty = _decimal(signal.quote_amount) / entry
        notional = _decimal(signal.quote_amount)
        source = "quote_amount/entry_price"
    elif signal.risk_amount and entry:
        stop = _stop_loss_price(signal, entry)
        if stop:
            per_unit_risk = abs(entry - stop)
            if per_unit_risk > 0:
                qty = _decimal(signal.risk_amount) / per_unit_risk
                source = "risk_amount/(entry-stop)"
    elif signal.risk_pct and equity and entry:
        stop = _stop_loss_price(signal, entry)
        if stop:
            per_unit_risk = abs(entry - stop)
            if per_unit_risk > 0:
                risk_amount = _decimal(equity) * _decimal(signal.risk_pct) / Decimal("100")
                qty = risk_amount / per_unit_risk
                source = "risk_pct*equity/(entry-stop)"

    if qty is not None:
        qty = qty.quantize(Decimal("0.00000001"))
        if entry:
            notional = notional or (qty * entry)
    if qty is None:
        warnings.append("provide base_amount, quote_amount+entry/mark, risk_amount+stop, or risk_pct+equity+stop to derive quantity")
    margin_required = (notional / leverage) if notional is not None and leverage > 0 else None
    return FuturesSizingResult(
        qty=qty,
        notional=notional,
        margin_required=margin_required,
        entry_price=entry,
        source=source,
        warnings=tuple(warnings),
    )


def _risk_assessment(
    signal: CryptoSignal,
    *,
    mark_price: Any | None,
    equity: Any | None,
    stop_price: Decimal | None,
) -> dict[str, Any]:
    if not (FuturesRiskConfig and FuturesTradeContext and assess_futures_trade):
        return {"available": False, "reason": "futures_risk module not available"}
    entry = _decimal(signal.price) or _decimal(mark_price)
    if not entry:
        return {"available": False, "reason": "entry or mark price required"}
    try:
        config = FuturesRiskConfig(account_equity=_decimal(equity) if equity else None)  # type: ignore[operator]
        context = FuturesTradeContext(  # type: ignore[operator]
            symbol=signal.symbol,
            side=signal.side,
            entry_price=entry,
            mark_price=_decimal(mark_price) or entry,
            leverage=_decimal(signal.leverage) or Decimal("1"),
            stop_loss_price=stop_price,
        )
        result = assess_futures_trade(context, config)  # type: ignore[operator]
        if hasattr(result, "to_dict"):
            return result.to_dict()
        if hasattr(result, "__dict__"):
            return dict(result.__dict__)
        return {"available": True, "result": str(result)}
    except Exception as exc:  # pragma: no cover - defensive against repo version drift.
        return {"available": False, "reason": str(exc)}


def _simple_full_bitunix_bracket(signal: CryptoSignal, targets: tuple[TakeProfitTarget, ...]) -> bool:
    has_synthetic = any(
        [
            signal.trailing_stop_pct,
            signal.trailing_stop_amount,
            signal.trailing_stop_price,
            signal.trailing_activation_pct,
            signal.trailing_activation_price,
            signal.breakeven_after_take_profit,
            signal.breakeven_trigger_pct,
            signal.profit_lock_after_take_profit_pct,
            signal.max_hold_marks,
            signal.trail_after_take_profit,
        ]
    )
    if has_synthetic:
        return False
    if len(targets) > 1:
        return False
    if targets and _decimal(targets[0].close_pct) != Decimal("100"):
        return False
    return True


def _stop_loss_price(signal: CryptoSignal, entry: Decimal | None) -> Decimal | None:
    if signal.stop_loss_price:
        return _decimal(signal.stop_loss_price)
    if signal.stop_loss_pct and entry:
        direction = Decimal("-1") if signal.side == "buy" else Decimal("1")
        return entry * (Decimal("1") + direction * _decimal(signal.stop_loss_pct) / Decimal("100"))
    return None


def _targets_with_prices(signal: CryptoSignal, entry: Decimal | None) -> tuple[TakeProfitTarget, ...]:
    targets: list[TakeProfitTarget] = []
    for target in signal.take_profit_targets:
        if target.trigger_price:
            targets.append(target)
            continue
        if target.pct and entry:
            direction = Decimal("1") if signal.side == "buy" else Decimal("-1")
            targets.append(
                TakeProfitTarget(
                    pct=target.pct,
                    trigger_price=entry * (Decimal("1") + direction * _decimal(target.pct) / Decimal("100")),
                    close_pct=target.close_pct,
                )
            )
    if not targets and signal.take_profit_price:
        targets.append(TakeProfitTarget(trigger_price=_decimal(signal.take_profit_price), close_pct=Decimal("100")))
    elif not targets and signal.take_profit_pct and entry:
        direction = Decimal("1") if signal.side == "buy" else Decimal("-1")
        targets.append(
            TakeProfitTarget(
                pct=signal.take_profit_pct,
                trigger_price=entry * (Decimal("1") + direction * _decimal(signal.take_profit_pct) / Decimal("100")),
                close_pct=Decimal("100"),
            )
        )
    return tuple(targets)


def _close_qty(qty: Decimal | None, close_pct: Any) -> Decimal | None:
    if qty is None:
        return None
    return (qty * _decimal(close_pct) / Decimal("100")).quantize(Decimal("0.00000001"))


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _decimal_or_none(value: Any) -> str | None:
    parsed = _decimal(value)
    if parsed is None:
        return None
    return _decimal_to_str(parsed)


def _decimal_to_str(value: Any) -> str:
    parsed = _decimal(value)
    if parsed is None:
        return str(value)
    return format(parsed.normalize(), "f")


def _exchange_symbol(symbol: str) -> str:
    return str(symbol).upper().replace("/", "")


def _opposite_side(side: str) -> str:
    return "sell" if str(side).lower() == "buy" else "buy"
