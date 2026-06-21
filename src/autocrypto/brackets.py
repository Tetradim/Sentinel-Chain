from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal


PROTECTIVE_EXIT_KINDS = {"stop_loss", "trailing_stop"}
PARTIAL_EXIT_KINDS = {"take_profit", "trailing_stop"}


def decimal_to_plain(value: Decimal) -> str:
    return format(value, "f")


def bool_value(value: bool, *, style: Literal["native", "string"]) -> bool | str:
    if style == "native":
        return value
    return str(value).lower()


def trailing_activation_price(lot: Any) -> Decimal | None:
    if lot.trailing_stop_pct is None and lot.trailing_stop_amount is None:
        return None
    if lot.trailing_activation_price is not None:
        return lot.trailing_activation_price
    if lot.trailing_activation_pct is None:
        return None
    direction = Decimal("1") if lot.direction == "long" else Decimal("-1")
    return lot.entry_price * (Decimal("1") + direction * lot.trailing_activation_pct / Decimal("100"))


def exit_distance(lot: Any, exit_order: Any, mark_price: Decimal) -> Decimal:
    if lot.direction == "long":
        if exit_order.kind in PROTECTIVE_EXIT_KINDS:
            return mark_price - exit_order.trigger_price
        return exit_order.trigger_price - mark_price
    if exit_order.kind in PROTECTIVE_EXIT_KINDS:
        return exit_order.trigger_price - mark_price
    return mark_price - exit_order.trigger_price


def exit_close_quantity(lot: Any, exit_order: Any) -> Decimal:
    if exit_order.kind not in PARTIAL_EXIT_KINDS:
        return lot.remaining_quantity
    target_quantity = lot.original_quantity * exit_order.close_pct / Decimal("100")
    return min(target_quantity, lot.remaining_quantity)


def exit_pnl(lot: Any, exit_order: Any, quantity: Decimal) -> Decimal:
    if lot.direction == "long":
        return (exit_order.trigger_price - lot.entry_price) * quantity
    return (lot.entry_price - exit_order.trigger_price) * quantity


def exit_intent(exit_order: Any) -> str:
    if exit_order.kind in PROTECTIVE_EXIT_KINDS:
        return "protective_exit"
    if exit_order.kind == "take_profit":
        return "profit_exit"
    if exit_order.kind == "time_exit":
        return "staleness_exit"
    return "conditional_exit"


def exit_ladder_sort_key(lot: Any, exit_order: Any) -> tuple[int, Decimal, str]:
    if exit_order.kind == "time_exit":
        return (1, Decimal("0"), exit_order.kind)
    price_key = exit_order.trigger_price if lot.direction == "long" else -exit_order.trigger_price
    return (0, price_key, exit_order.kind)


def active_exit_payload(
    lot: Any,
    exit_order: Any,
    *,
    bool_style: Literal["native", "string"] = "string",
    include_entry: bool = True,
    include_signal: bool = True,
    include_close_pct: bool = True,
    include_oca_group: bool = True,
) -> dict[str, Any]:
    is_trailing = exit_order.kind == "trailing_stop"
    activation_price = trailing_activation_price(lot) if is_trailing else None
    payload = {
        "symbol": lot.symbol,
        "direction": lot.direction,
        "kind": exit_order.kind,
        "trigger_price": str(exit_order.trigger_price),
        "status": exit_order.status,
        "initial_trailing_stop_price": str(lot.trailing_stop_price)
        if is_trailing and lot.trailing_stop_price
        else None,
        "trailing_stop_pct": str(lot.trailing_stop_pct) if is_trailing and lot.trailing_stop_pct else None,
        "trailing_stop_amount": str(lot.trailing_stop_amount) if is_trailing and lot.trailing_stop_amount else None,
        "trailing_step_pct": str(lot.trailing_step_pct) if is_trailing and lot.trailing_step_pct else None,
        "trailing_step_amount": str(lot.trailing_step_amount) if is_trailing and lot.trailing_step_amount else None,
        "trailing_activation_pct": str(lot.trailing_activation_pct)
        if is_trailing and lot.trailing_activation_pct
        else None,
        "trailing_activation_price": str(activation_price) if activation_price is not None else None,
        "configured_trailing_activation_price": str(lot.trailing_activation_price)
        if is_trailing and lot.trailing_activation_price
        else None,
        "trail_after_take_profit": bool_value(lot.trail_after_take_profit, style=bool_style) if is_trailing else None,
        "take_profit_filled": bool_value(lot.take_profit_filled, style=bool_style) if is_trailing else None,
        "trailing_activated": bool_value(lot.trailing_activated, style=bool_style) if is_trailing else None,
        "high_water_mark": str(lot.high_water_mark) if is_trailing and lot.high_water_mark else None,
        "low_water_mark": str(lot.low_water_mark) if is_trailing and lot.low_water_mark else None,
        "breakeven_after_take_profit": bool_value(lot.breakeven_after_take_profit, style=bool_style),
        "breakeven_applied": bool_value(lot.breakeven_applied, style=bool_style),
        "max_hold_marks": lot.max_hold_marks if exit_order.kind == "time_exit" else None,
        "marks_seen": lot.marks_seen if exit_order.kind == "time_exit" else None,
        "marks_remaining": max(lot.max_hold_marks - lot.marks_seen, 0)
        if exit_order.kind == "time_exit" and lot.max_hold_marks is not None
        else None,
        "remaining_quantity": str(lot.remaining_quantity),
    }
    if include_signal:
        payload["signal_id"] = lot.signal_id
    if include_entry:
        payload["entry_price"] = str(lot.entry_price)
    if include_close_pct:
        payload["close_pct"] = str(exit_order.close_pct)
    if include_oca_group:
        payload["oca_group"] = exit_order.oca_group
    return payload


def exit_order_payload(exit_order: Any) -> dict[str, Any]:
    return {
        "kind": exit_order.kind,
        "trigger_price": str(exit_order.trigger_price),
        "close_pct": str(exit_order.close_pct),
        "oca_group": exit_order.oca_group,
        "status": exit_order.status,
    }


def bracket_coverage_payload(lot: Any) -> dict[str, Any]:
    open_exits = [exit_order for exit_order in lot.exit_orders if exit_order.status == "open"]
    take_profit_close_pct = sum(
        (exit_order.close_pct for exit_order in open_exits if exit_order.kind == "take_profit"),
        Decimal("0"),
    )
    trailing_close_pct = sum(
        (exit_order.close_pct for exit_order in open_exits if exit_order.kind == "trailing_stop"),
        Decimal("0"),
    )
    protective_close_pct = max(
        (exit_order.close_pct for exit_order in open_exits if exit_order.kind in PROTECTIVE_EXIT_KINDS),
        default=Decimal("0"),
    )
    full_close_exit_count = sum(
        1
        for exit_order in open_exits
        if exit_order.kind != "time_exit" and exit_close_quantity(lot, exit_order) >= lot.remaining_quantity
    )
    partial_close_exit_count = sum(
        1
        for exit_order in open_exits
        if exit_order.kind != "time_exit" and exit_close_quantity(lot, exit_order) < lot.remaining_quantity
    )
    residual_after_take_profit_pct = max(Decimal("100") - take_profit_close_pct, Decimal("0"))
    residual_after_take_profit_quantity = lot.original_quantity * residual_after_take_profit_pct / Decimal("100")
    residual_after_take_profit_quantity = min(residual_after_take_profit_quantity, lot.remaining_quantity)
    return {
        "signal_id": lot.signal_id,
        "symbol": lot.symbol,
        "direction": lot.direction,
        "remaining_quantity": str(lot.remaining_quantity),
        "take_profit_close_pct": decimal_to_plain(take_profit_close_pct),
        "trailing_stop_close_pct": decimal_to_plain(trailing_close_pct) if trailing_close_pct else None,
        "protective_close_pct": decimal_to_plain(protective_close_pct),
        "residual_after_take_profit_pct": decimal_to_plain(residual_after_take_profit_pct),
        "residual_after_take_profit_quantity": decimal_to_plain(residual_after_take_profit_quantity),
        "residual_after_take_profit_notional": decimal_to_plain(
            residual_after_take_profit_quantity * lot.entry_price
        ),
        "has_full_protective_exit": any(
            exit_order.kind in PROTECTIVE_EXIT_KINDS and exit_close_quantity(lot, exit_order) >= lot.remaining_quantity
            for exit_order in open_exits
        ),
        "has_full_profit_exit": take_profit_close_pct >= Decimal("100"),
        "has_time_exit": any(exit_order.kind == "time_exit" for exit_order in lot.exit_orders),
        "full_close_exit_count": full_close_exit_count,
        "partial_close_exit_count": partial_close_exit_count,
        "coverage_notes": bracket_coverage_notes(lot, open_exits, take_profit_close_pct),
    }


def bracket_coverage_notes(lot: Any, open_exits: list[Any], take_profit_close_pct: Decimal) -> list[str]:
    notes: list[str] = []
    if not any(exit_order.kind in PROTECTIVE_EXIT_KINDS for exit_order in open_exits):
        notes.append("no_open_protective_exit")
    if take_profit_close_pct == 0:
        notes.append("no_open_take_profit_exit")
    elif take_profit_close_pct < Decimal("100"):
        notes.append("take_profit_plan_leaves_residual")
    if any(
        exit_order.kind in PARTIAL_EXIT_KINDS and exit_close_quantity(lot, exit_order) < lot.remaining_quantity
        for exit_order in open_exits
    ):
        notes.append("contains_partial_exit")
    if any(exit_order.kind == "time_exit" for exit_order in lot.exit_orders):
        notes.append("contains_paper_time_exit")
    return notes


def trailing_ratchet_impacts(live_lots: list[Any], preview_lots: list[Any]) -> list[dict[str, Any]]:
    impacts: list[dict[str, Any]] = []
    for live_lot in live_lots:
        preview_lot = next((lot for lot in preview_lots if lot.signal_id == live_lot.signal_id), None)
        if preview_lot is None:
            continue
        live_trail = next((exit_order for exit_order in live_lot.exit_orders if exit_order.kind == "trailing_stop"), None)
        preview_trail = next((exit_order for exit_order in preview_lot.exit_orders if exit_order.kind == "trailing_stop"), None)
        if live_trail is None or preview_trail is None or live_trail.trigger_price == preview_trail.trigger_price:
            continue
        impacts.append(
            {
                "signal_id": live_lot.signal_id,
                "before_trigger_price": str(live_trail.trigger_price),
                "after_trigger_price": str(preview_trail.trigger_price),
                "trigger_change": decimal_to_plain(preview_trail.trigger_price - live_trail.trigger_price)
                if live_lot.direction == "long"
                else decimal_to_plain(live_trail.trigger_price - preview_trail.trigger_price),
                "status_before": live_trail.status,
                "status_after": preview_trail.status,
            }
        )
    return impacts
