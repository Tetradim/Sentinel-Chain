from __future__ import annotations

from decimal import Decimal
from typing import Any

from sentinel_chain.api.serializers import decimal_to_plain as _decimal_to_plain
from sentinel_chain.api.serializers import money as _money
from sentinel_chain.brackets import (
    active_exit_payload,
    bracket_coverage_payload,
    exit_close_quantity,
    exit_distance,
    exit_intent,
    exit_ladder_sort_key,
    exit_pnl,
    trailing_activation_price,
    trailing_ratchet_impacts,
)


def _active_exits_to_dict(
    lots: list[Any],
    *,
    signal_id: str | None = None,
    mark_price: Decimal | None = None,
) -> list[dict[str, Any]]:
    return [
        _active_exit_to_dict(lot, exit_order, mark_price=mark_price)
        for lot in sorted(lots, key=lambda item: (item.symbol, item.signal_id))
        if lot.remaining_quantity > 0 and (signal_id is None or lot.signal_id == signal_id)
        for exit_order in lot.exit_orders
    ]


def _active_exit_to_dict(lot: Any, exit_order: Any, *, mark_price: Decimal | None) -> dict[str, Any]:
    activation_price = trailing_activation_price(lot) if exit_order.kind == "trailing_stop" else None
    distance = exit_distance(lot, exit_order, mark_price) if mark_price is not None else None
    trailing_telemetry = _trailing_telemetry(lot, exit_order, mark_price=mark_price)
    return {
        **active_exit_payload(lot, exit_order, bool_style="string"),
        "computed_trailing_activation_price": str(activation_price) if activation_price is not None else None,
        "next_trailing_trigger": trailing_telemetry["next_trailing_trigger"],
        "next_trailing_trigger_change": trailing_telemetry["next_trailing_trigger_change"],
        "trailing_step_required": trailing_telemetry["trailing_step_required"],
        "trailing_ratchet_ready_at_mark": trailing_telemetry["trailing_ratchet_ready_at_mark"],
        "trailing_activation_ready_at_mark": trailing_telemetry["trailing_activation_ready_at_mark"],
        "distance_to_trigger": str(distance) if distance is not None else None,
        "distance_to_trigger_pct": str(distance / mark_price * Decimal("100"))
        if distance is not None and mark_price is not None and mark_price > 0
        else None,
        "breakeven_trigger_pct": str(lot.breakeven_trigger_pct) if lot.breakeven_trigger_pct else None,
        "profit_lock_after_take_profit_pct": str(lot.profit_lock_after_take_profit_pct)
        if lot.profit_lock_after_take_profit_pct
        else None,
    }


def _trailing_preview_snapshot(
    lots: list[Any],
    *,
    signal_id: str,
    mark_price: Decimal | None,
) -> list[dict[str, Any]]:
    return [
        _active_exit_to_dict(lot, exit_order, mark_price=mark_price)
        for lot in lots
        if lot.signal_id == signal_id and lot.remaining_quantity > 0
        for exit_order in lot.exit_orders
        if exit_order.kind == "trailing_stop"
    ]


def _trailing_snapshot_ratcheted(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> bool:
    before_by_group = _trailing_snapshot_by_group(before)
    after_by_group = _trailing_snapshot_by_group(after)
    for key, before_row in before_by_group.items():
        after_row = after_by_group.get(key)
        if after_row is None:
            continue
        if before_row.get("trigger_price") != after_row.get("trigger_price"):
            return True
    return False


def _trailing_snapshot_activated(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> bool:
    before_by_group = _trailing_snapshot_by_group(before)
    after_by_group = _trailing_snapshot_by_group(after)
    for key, before_row in before_by_group.items():
        after_row = after_by_group.get(key)
        if after_row is None:
            continue
        if before_row.get("status") != "open" and after_row.get("status") == "open":
            return True
        if before_row.get("trailing_activated") == "false" and after_row.get("trailing_activated") == "true":
            return True
    return False


def _trailing_snapshot_by_group(rows: list[dict[str, Any]]) -> dict[tuple[str | None, str | None], dict[str, Any]]:
    return {(row.get("signal_id"), row.get("oca_group")): row for row in rows}


def _active_brackets_to_dict(lots: list[Any]) -> list[dict[str, Any]]:
    brackets: list[dict[str, Any]] = []
    for lot in sorted(lots, key=lambda item: (item.symbol, item.signal_id)):
        if lot.remaining_quantity <= 0 or not lot.exit_orders:
            continue
        brackets.append(
            {
                "signal_id": lot.signal_id,
                "symbol": lot.symbol,
                "direction": lot.direction,
                "remaining_quantity": str(lot.remaining_quantity),
                "entry_price": str(lot.entry_price),
                "summary": _bracket_summary(lot),
                "exits": _active_exits_to_dict([lot], signal_id=lot.signal_id),
            }
        )
    return brackets


def _bracket_exit_ladder_to_dict(lot: Any, *, mark_price: Decimal | None = None) -> dict[str, Any]:
    ordered_exits = sorted(lot.exit_orders, key=lambda exit_order: exit_ladder_sort_key(lot, exit_order))
    rows = [
        _exit_ladder_row(lot, exit_order, trigger_order=index + 1, mark_price=mark_price)
        for index, exit_order in enumerate(ordered_exits)
    ]
    return {
        "signal_id": lot.signal_id,
        "symbol": lot.symbol,
        "direction": lot.direction,
        "entry_price": str(lot.entry_price),
        "remaining_quantity": str(lot.remaining_quantity),
        "remaining_notional": _decimal_to_plain(lot.remaining_quantity * lot.entry_price),
        "exit_count": len(rows),
        "full_close_count": sum(1 for row in rows if row["would_close_remaining"]),
        "partial_close_count": sum(1 for row in rows if not row["would_close_remaining"]),
        "rows": rows,
    }


def _bracket_decision_support_to_dict(lot: Any, *, mark_price: Decimal | None = None) -> dict[str, Any]:
    rows = [
        _decision_support_row(lot, exit_order, trigger_order=index + 1, mark_price=mark_price)
        for index, exit_order in enumerate(
            sorted(lot.exit_orders, key=lambda exit_order: exit_ladder_sort_key(lot, exit_order))
        )
    ]
    next_trigger = next((row for row in rows if row["status"] == "open"), rows[0] if rows else None)
    trailing_rows = [row for row in rows if row["kind"] == "trailing_stop"]
    return {
        "signal_id": lot.signal_id,
        "symbol": lot.symbol,
        "direction": lot.direction,
        "entry_price": str(lot.entry_price),
        "remaining_quantity": str(lot.remaining_quantity),
        "summary": _bracket_summary(lot),
        "health": _bracket_health_row(lot),
        "next_open_trigger": next_trigger,
        "trailing": trailing_rows,
        "trigger_sequence": rows,
    }


def _bracket_coverage_to_dict(lot: Any) -> dict[str, Any]:
    return bracket_coverage_payload(lot)


def _bracket_preview_impact(
    lots: list[Any],
    *,
    preview_exchange: Any | None,
    signal_id: str,
    would_trigger: list[dict[str, Any]],
) -> dict[str, Any]:
    preview_lots = [
        lot
        for lot in (preview_exchange.lots if preview_exchange is not None else [])
        if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
    ]
    before_quantity = sum((lot.remaining_quantity for lot in lots), Decimal("0"))
    after_quantity = sum((lot.remaining_quantity for lot in preview_lots), Decimal("0"))
    return {
        "mutates_state": False,
        "will_trigger": bool(would_trigger),
        "triggered_kinds": [item["kind"] for item in would_trigger],
        "will_close_bracket": before_quantity > 0 and after_quantity == 0,
        "remaining_quantity_before": _decimal_to_plain(before_quantity),
        "remaining_quantity_after": _decimal_to_plain(after_quantity),
        "quantity_delta": _decimal_to_plain(after_quantity - before_quantity),
        "trailing_ratchets": trailing_ratchet_impacts(lots, preview_lots),
    }


def _decision_support_row(
    lot: Any,
    exit_order: Any,
    *,
    trigger_order: int,
    mark_price: Decimal | None,
) -> dict[str, Any]:
    row = _exit_ladder_row(lot, exit_order, trigger_order=trigger_order, mark_price=mark_price)
    row["protective"] = exit_order.kind in {"stop_loss", "trailing_stop"}
    row["profit_taking"] = exit_order.kind == "take_profit"
    row["paper_only"] = True
    row.update(_trailing_telemetry(lot, exit_order, mark_price=mark_price))
    return row


def _exit_ladder_row(
    lot: Any,
    exit_order: Any,
    *,
    trigger_order: int,
    mark_price: Decimal | None,
) -> dict[str, Any]:
    quantity = exit_close_quantity(lot, exit_order)
    estimated_notional = quantity * exit_order.trigger_price
    estimated_pnl = exit_pnl(lot, exit_order, quantity)
    distance = exit_distance(lot, exit_order, mark_price) if mark_price is not None else None
    return {
        "trigger_order": trigger_order,
        "kind": exit_order.kind,
        "intent": exit_intent(exit_order),
        "status": exit_order.status,
        "trigger_price": str(exit_order.trigger_price),
        "close_pct": str(exit_order.close_pct),
        "estimated_exit_quantity": _decimal_to_plain(quantity),
        "estimated_exit_notional": _decimal_to_plain(estimated_notional),
        "estimated_pnl": _decimal_to_plain(estimated_pnl),
        "estimated_pnl_pct": _decimal_to_plain(estimated_pnl / (quantity * lot.entry_price) * Decimal("100"))
        if quantity > 0 and lot.entry_price > 0
        else None,
        "would_close_remaining": quantity >= lot.remaining_quantity,
        "oca_group": exit_order.oca_group,
        "distance_to_trigger": str(distance) if distance is not None else None,
        "distance_to_trigger_pct": str(distance / mark_price * Decimal("100"))
        if distance is not None and mark_price is not None and mark_price > 0
        else None,
        "trailing_activation_price": str(trailing_activation_price(lot))
        if exit_order.kind == "trailing_stop" and trailing_activation_price(lot) is not None
        else None,
        "marks_remaining": max(lot.max_hold_marks - lot.marks_seen, 0)
        if exit_order.kind == "time_exit" and lot.max_hold_marks is not None
        else None,
        **_trailing_telemetry(lot, exit_order, mark_price=mark_price),
    }


def _trailing_telemetry(lot: Any, exit_order: Any, *, mark_price: Decimal | None) -> dict[str, Any]:
    empty = {
        "next_trailing_trigger": None,
        "next_trailing_trigger_change": None,
        "trailing_step_required": None,
        "trailing_ratchet_ready_at_mark": None,
        "trailing_activation_ready_at_mark": None,
    }
    if exit_order.kind != "trailing_stop":
        return empty

    activation_ready = _trailing_activation_ready(lot, mark_price) if mark_price is not None else None
    step_required = _trailing_step_required(lot, exit_order.trigger_price)
    if mark_price is None or exit_order.status != "open":
        return {
            **empty,
            "trailing_step_required": _decimal_to_plain(step_required) if step_required is not None else None,
            "trailing_activation_ready_at_mark": str(activation_ready).lower() if activation_ready is not None else None,
        }

    next_trigger = _candidate_trailing_trigger(lot, mark_price)
    if next_trigger is None:
        return {
            **empty,
            "trailing_step_required": _decimal_to_plain(step_required) if step_required is not None else None,
            "trailing_ratchet_ready_at_mark": "false",
            "trailing_activation_ready_at_mark": str(activation_ready).lower() if activation_ready is not None else None,
        }
    change = next_trigger - exit_order.trigger_price if lot.direction == "long" else exit_order.trigger_price - next_trigger
    ratchet_ready = change > 0 and (step_required is None or change >= step_required)
    return {
        "next_trailing_trigger": str(next_trigger) if ratchet_ready else None,
        "next_trailing_trigger_change": _decimal_to_plain(change) if change > 0 else None,
        "trailing_step_required": _decimal_to_plain(step_required) if step_required is not None else None,
        "trailing_ratchet_ready_at_mark": str(ratchet_ready).lower(),
        "trailing_activation_ready_at_mark": str(activation_ready).lower() if activation_ready is not None else None,
    }


def _trailing_activation_ready(lot: Any, mark_price: Decimal | None) -> bool | None:
    activation_price = trailing_activation_price(lot)
    if activation_price is None or mark_price is None:
        return None
    return mark_price >= activation_price if lot.direction == "long" else mark_price <= activation_price


def _candidate_trailing_trigger(lot: Any, mark_price: Decimal) -> Decimal | None:
    if lot.trailing_stop_pct is None and lot.trailing_stop_amount is None:
        return None
    if lot.direction == "long":
        water_mark = max(lot.high_water_mark or lot.entry_price, mark_price)
        distance = _trailing_distance(lot, water_mark)
        return _money(water_mark - distance)
    water_mark = min(lot.low_water_mark or lot.entry_price, mark_price)
    distance = _trailing_distance(lot, water_mark)
    return _money(water_mark + distance)


def _trailing_distance(lot: Any, price: Decimal) -> Decimal:
    if lot.trailing_stop_amount is not None:
        return lot.trailing_stop_amount
    if lot.trailing_stop_pct is None:
        return Decimal("0")
    return price * lot.trailing_stop_pct / Decimal("100")


def _trailing_step_required(lot: Any, current_trigger: Decimal) -> Decimal | None:
    if lot.trailing_step_amount is not None:
        return lot.trailing_step_amount
    if lot.trailing_step_pct is not None:
        return current_trigger * lot.trailing_step_pct / Decimal("100")
    return Decimal("0")


def _bracket_risk_summary(lots: list[Any]) -> dict[str, Any]:
    active_lots = [lot for lot in lots if lot.remaining_quantity > 0 and lot.exit_orders]
    by_symbol: dict[str, dict[str, Any]] = {}
    totals = _empty_bracket_totals()
    for lot in active_lots:
        summary = _bracket_summary(lot)
        _accumulate_bracket_totals(totals, lot, summary)
        symbol_totals = by_symbol.setdefault(lot.symbol, _empty_bracket_totals(symbol=lot.symbol))
        _accumulate_bracket_totals(symbol_totals, lot, summary)

    return {
        "bracket_count": len(active_lots),
        "long_bracket_count": sum(1 for lot in active_lots if lot.direction == "long"),
        "short_bracket_count": sum(1 for lot in active_lots if lot.direction == "short"),
        "exit_count": sum(len(lot.exit_orders) for lot in active_lots),
        "trailing_stop_count": sum(
            1 for lot in active_lots for exit_order in lot.exit_orders if exit_order.kind == "trailing_stop"
        ),
        "pending_trailing_stop_count": sum(
            1
            for lot in active_lots
            for exit_order in lot.exit_orders
            if exit_order.kind == "trailing_stop" and exit_order.status == "pending_activation"
        ),
        "time_stop_count": sum(1 for lot in active_lots for exit_order in lot.exit_orders if exit_order.kind == "time_exit"),
        "totals": _bracket_totals_to_dict(totals),
        "by_symbol": [_bracket_totals_to_dict(by_symbol[symbol]) for symbol in sorted(by_symbol)],
    }


def _bracket_health(lots: list[Any]) -> dict[str, Any]:
    active_lots = [lot for lot in lots if lot.remaining_quantity > 0 and lot.exit_orders]
    oca_conflict_signal_ids = _oca_conflict_signal_ids(active_lots)
    rows = [
        _bracket_health_row(lot, oca_conflict_signal_ids=oca_conflict_signal_ids)
        for lot in sorted(active_lots, key=lambda item: (item.symbol, item.signal_id))
    ]
    issue_counts: dict[str, int] = {}
    for row in rows:
        for issue in row["issues"]:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    return {
        "bracket_count": len(rows),
        "healthy_count": sum(1 for row in rows if row["status"] == "healthy"),
        "attention_count": sum(1 for row in rows if row["status"] == "attention"),
        "issue_counts": issue_counts,
        "brackets": rows,
    }


def _bracket_health_row(lot: Any, *, oca_conflict_signal_ids: set[str] | None = None) -> dict[str, Any]:
    summary = _bracket_summary(lot)
    protective_exit = _nearest_protective_exit(lot)
    first_reward_ratio = _decimal_or_none(summary["first_target_reward_risk_ratio"])
    total_reward_ratio = _decimal_or_none(summary["total_target_reward_risk_ratio"])
    open_take_profit_count = sum(
        1 for exit_order in lot.exit_orders if exit_order.kind == "take_profit" and exit_order.status == "open"
    )
    pending_trailing_count = sum(
        1
        for exit_order in lot.exit_orders
        if exit_order.kind == "trailing_stop" and exit_order.status in {"pending_activation", "pending_take_profit"}
    )
    issues: list[str] = []
    if protective_exit is None:
        issues.append("no_open_protective_exit")
    elif _decimal_or_zero(summary["worst_case_loss"]) > 0:
        issues.append("protective_exit_still_at_risk")
    if pending_trailing_count:
        issues.append("trailing_stop_pending")
    if open_take_profit_count == 0:
        issues.append("no_open_take_profit_exit")
    elif first_reward_ratio is not None and first_reward_ratio < 1:
        issues.append("first_target_reward_below_risk")
    if total_reward_ratio is not None and total_reward_ratio < 1:
        issues.append("total_target_reward_below_risk")
    if oca_conflict_signal_ids and lot.signal_id in oca_conflict_signal_ids:
        issues.append("oca_group_reused_across_brackets")
    return {
        "signal_id": lot.signal_id,
        "symbol": lot.symbol,
        "direction": lot.direction,
        "status": "attention" if issues else "healthy",
        "issues": issues,
        "remaining_quantity": str(lot.remaining_quantity),
        "remaining_notional": summary["remaining_notional"],
        "protective_exit_kind": summary["protective_exit_kind"],
        "protective_trigger_price": summary["protective_trigger_price"],
        "worst_case_loss": summary["worst_case_loss"],
        "protective_locked_pnl": summary["protective_locked_pnl"],
        "first_target_reward_risk_ratio": summary["first_target_reward_risk_ratio"],
        "total_target_reward_risk_ratio": summary["total_target_reward_risk_ratio"],
        "open_take_profit_count": open_take_profit_count,
        "pending_trailing_count": pending_trailing_count,
        "oca_groups": _lot_oca_groups(lot),
    }


def _bracket_oca_groups(lots: list[Any]) -> dict[str, Any]:
    active_lots = [lot for lot in lots if lot.remaining_quantity > 0 and lot.exit_orders]
    groups: dict[str, dict[str, Any]] = {}
    for lot in active_lots:
        for group in _lot_oca_groups(lot):
            row = groups.setdefault(
                group,
                {
                    "oca_group": group,
                    "signal_ids": set(),
                    "symbols": set(),
                    "directions": set(),
                    "exit_count": 0,
                },
            )
            row["signal_ids"].add(lot.signal_id)
            row["symbols"].add(lot.symbol)
            row["directions"].add(lot.direction)
            row["exit_count"] += sum(1 for exit_order in lot.exit_orders if exit_order.oca_group == group)

    rows: list[dict[str, Any]] = []
    for group in sorted(groups):
        row = groups[group]
        signal_ids = sorted(row["signal_ids"])
        symbols = sorted(row["symbols"])
        directions = sorted(row["directions"])
        notes: list[str] = []
        if len(signal_ids) > 1:
            notes.append("oca_group_reused_across_brackets")
        if len(symbols) > 1:
            notes.append("oca_group_spans_symbols")
        if len(directions) > 1:
            notes.append("oca_group_spans_directions")
        rows.append(
            {
                "oca_group": group,
                "bracket_count": len(signal_ids),
                "exit_count": row["exit_count"],
                "signal_ids": signal_ids,
                "symbols": symbols,
                "directions": directions,
                "reused_across_brackets": len(signal_ids) > 1,
                "notes": notes,
            }
        )
    return {
        "group_count": len(rows),
        "reused_group_count": sum(1 for row in rows if row["reused_across_brackets"]),
        "groups": rows,
    }


def _oca_conflict_signal_ids(lots: list[Any]) -> set[str]:
    conflicts: set[str] = set()
    for row in _bracket_oca_groups(lots)["groups"]:
        if row["reused_across_brackets"]:
            conflicts.update(row["signal_ids"])
    return conflicts


def _lot_oca_groups(lot: Any) -> list[str]:
    return sorted(
        {
            exit_order.oca_group
            for exit_order in lot.exit_orders
            if exit_order.status not in {"canceled", "filled"} and exit_order.oca_group
        }
    )


def _empty_bracket_totals(*, symbol: str | None = None) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "bracket_count": 0,
        "remaining_notional": Decimal("0"),
        "worst_case_loss": Decimal("0"),
        "protective_locked_pnl": Decimal("0"),
        "first_target_reward": Decimal("0"),
        "total_target_reward": Decimal("0"),
    }


def _accumulate_bracket_totals(totals: dict[str, Any], lot: Any, summary: dict[str, str | None]) -> None:
    totals["bracket_count"] += 1
    totals["remaining_notional"] += lot.remaining_quantity * lot.entry_price
    totals["worst_case_loss"] += _decimal_or_zero(summary["worst_case_loss"])
    totals["protective_locked_pnl"] += _decimal_or_zero(summary["protective_locked_pnl"])
    totals["first_target_reward"] += _decimal_or_zero(summary["first_target_reward"])
    totals["total_target_reward"] += _decimal_or_zero(summary["total_target_reward"])


def _bracket_totals_to_dict(totals: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "bracket_count": totals["bracket_count"],
        "remaining_notional": _decimal_to_plain(totals["remaining_notional"]),
        "worst_case_loss": _decimal_to_plain(totals["worst_case_loss"]),
        "protective_locked_pnl": _decimal_to_plain(totals["protective_locked_pnl"]),
        "first_target_reward": _decimal_to_plain(totals["first_target_reward"]),
        "first_target_reward_risk_ratio": _decimal_to_plain(
            totals["first_target_reward"] / totals["worst_case_loss"]
        )
        if totals["worst_case_loss"] > 0
        else None,
        "total_target_reward": _decimal_to_plain(totals["total_target_reward"]),
        "total_target_reward_risk_ratio": _decimal_to_plain(
            totals["total_target_reward"] / totals["worst_case_loss"]
        )
        if totals["worst_case_loss"] > 0
        else None,
    }
    if totals["symbol"] is not None:
        payload["symbol"] = totals["symbol"]
    return payload


def _decimal_or_zero(value: str | None) -> Decimal:
    return Decimal(value) if value is not None else Decimal("0")


def _decimal_or_none(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def _bracket_summary(lot: Any) -> dict[str, str | None]:
    remaining_notional = lot.remaining_quantity * lot.entry_price
    protective_exit = _nearest_protective_exit(lot)
    first_target = _nearest_take_profit_exit(lot)
    worst_case_loss = _lot_protective_loss(lot, protective_exit)
    protective_locked_pnl = _lot_protective_locked_pnl(lot, protective_exit)
    protective_distance_pct = _lot_protective_distance_pct(lot, protective_exit)
    first_target_reward = _lot_target_reward(lot, first_target)
    total_target_reward = _lot_total_target_reward(lot)
    return {
        "remaining_notional": _decimal_to_plain(remaining_notional),
        "protective_exit_kind": protective_exit.kind if protective_exit is not None else None,
        "protective_trigger_price": str(protective_exit.trigger_price) if protective_exit is not None else None,
        "protective_distance_pct": _decimal_to_plain(protective_distance_pct)
        if protective_distance_pct is not None
        else None,
        "worst_case_loss": _decimal_to_plain(worst_case_loss) if worst_case_loss is not None else None,
        "protective_locked_pnl": _decimal_to_plain(protective_locked_pnl)
        if protective_locked_pnl is not None
        else None,
        "first_target_price": str(first_target.trigger_price) if first_target is not None else None,
        "first_target_reward": _decimal_to_plain(first_target_reward) if first_target_reward is not None else None,
        "first_target_reward_risk_ratio": _decimal_to_plain(first_target_reward / worst_case_loss)
        if first_target_reward is not None and worst_case_loss is not None and worst_case_loss > 0
        else None,
        "total_target_reward": _decimal_to_plain(total_target_reward) if total_target_reward is not None else None,
        "total_target_reward_risk_ratio": _decimal_to_plain(total_target_reward / worst_case_loss)
        if total_target_reward is not None and worst_case_loss is not None and worst_case_loss > 0
        else None,
    }


def _nearest_protective_exit(lot: Any) -> Any | None:
    protective_exits = [
        exit_order
        for exit_order in lot.exit_orders
        if exit_order.kind in {"stop_loss", "trailing_stop"} and exit_order.status == "open"
    ]
    if lot.direction == "long":
        return max(protective_exits, key=lambda item: item.trigger_price, default=None)
    return min(protective_exits, key=lambda item: item.trigger_price, default=None)


def _nearest_take_profit_exit(lot: Any) -> Any | None:
    targets = [
        exit_order
        for exit_order in lot.exit_orders
        if exit_order.kind == "take_profit" and exit_order.status != "canceled"
    ]
    if lot.direction == "long":
        return min(targets, key=lambda item: item.trigger_price, default=None)
    return max(targets, key=lambda item: item.trigger_price, default=None)


def _lot_protective_loss(lot: Any, protective_exit: Any | None) -> Decimal | None:
    if protective_exit is None:
        return None
    if lot.direction == "long":
        distance = lot.entry_price - protective_exit.trigger_price
    else:
        distance = protective_exit.trigger_price - lot.entry_price
    return max(distance, Decimal("0")) * lot.remaining_quantity


def _lot_protective_locked_pnl(lot: Any, protective_exit: Any | None) -> Decimal | None:
    if protective_exit is None:
        return None
    if lot.direction == "long":
        distance = protective_exit.trigger_price - lot.entry_price
    else:
        distance = lot.entry_price - protective_exit.trigger_price
    return distance * lot.remaining_quantity


def _lot_protective_distance_pct(lot: Any, protective_exit: Any | None) -> Decimal | None:
    if protective_exit is None or lot.entry_price <= 0:
        return None
    if lot.direction == "long":
        distance = lot.entry_price - protective_exit.trigger_price
    else:
        distance = protective_exit.trigger_price - lot.entry_price
    return distance / lot.entry_price * Decimal("100")


def _lot_target_reward(lot: Any, target_exit: Any | None) -> Decimal | None:
    if target_exit is None:
        return None
    if lot.direction == "long":
        distance = target_exit.trigger_price - lot.entry_price
    else:
        distance = lot.entry_price - target_exit.trigger_price
    if distance <= 0:
        return None
    target_quantity = min(lot.remaining_quantity, lot.original_quantity * target_exit.close_pct / Decimal("100"))
    return distance * target_quantity


def _lot_total_target_reward(lot: Any) -> Decimal | None:
    rewards = [
        reward
        for exit_order in lot.exit_orders
        if exit_order.kind == "take_profit" and exit_order.status != "canceled"
        for reward in [_lot_target_reward(lot, exit_order)]
        if reward is not None
    ]
    if not rewards:
        return None
    return sum(rewards, Decimal("0"))


active_brackets_to_dict = _active_brackets_to_dict
active_exits_to_dict = _active_exits_to_dict
active_exit_to_dict = _active_exit_to_dict
bracket_coverage_to_dict = _bracket_coverage_to_dict
bracket_decision_support_to_dict = _bracket_decision_support_to_dict
bracket_exit_ladder_to_dict = _bracket_exit_ladder_to_dict
bracket_health = _bracket_health
bracket_health_row = _bracket_health_row
bracket_oca_groups = _bracket_oca_groups
bracket_preview_impact = _bracket_preview_impact
bracket_risk_summary = _bracket_risk_summary
bracket_summary = _bracket_summary
candidate_trailing_trigger = _candidate_trailing_trigger
decimal_or_none = _decimal_or_none
decimal_or_zero = _decimal_or_zero
empty_bracket_totals = _empty_bracket_totals
lot_oca_groups = _lot_oca_groups
nearest_protective_exit = _nearest_protective_exit
nearest_take_profit_exit = _nearest_take_profit_exit
trailing_activation_ready = _trailing_activation_ready
trailing_distance = _trailing_distance
trailing_preview_snapshot = _trailing_preview_snapshot
trailing_snapshot_activated = _trailing_snapshot_activated
trailing_snapshot_ratcheted = _trailing_snapshot_ratcheted
trailing_step_required = _trailing_step_required
