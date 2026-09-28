from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sentinel_chain.brackets import decimal_to_plain as _bracket_decimal_to_plain
from sentinel_chain.execution import build_exit_orders
from sentinel_chain.risk import AccountState, RiskConfig, RiskDecision, evaluate_signal
from sentinel_chain.signals import CryptoSignal


def risk_config_to_dict(config: RiskConfig) -> dict[str, Any]:
    return {
        "max_order_notional": str(config.max_order_notional),
        "max_open_notional": str(config.max_open_notional),
        "max_symbol_open_notional": str(config.max_symbol_open_notional),
        "max_open_risk_amount": str(config.max_open_risk_amount),
        "max_open_risk_equity_pct": str(config.max_open_risk_equity_pct),
        "max_position_equity_pct": str(config.max_position_equity_pct),
        "max_risk_amount": str(config.max_risk_amount),
        "max_risk_per_trade_pct": str(config.max_risk_per_trade_pct),
        "max_entry_volatility_pct": str(config.max_entry_volatility_pct),
        "max_leverage": str(config.max_leverage),
        "max_daily_loss": str(config.max_daily_loss),
        "max_consecutive_losses": config.max_consecutive_losses,
        "require_stop_loss": config.require_stop_loss,
        "max_stop_loss_pct": str(config.max_stop_loss_pct),
        "max_trailing_stop_pct": str(config.max_trailing_stop_pct),
        "min_reward_risk_ratio": str(config.min_reward_risk_ratio),
        "min_total_reward_risk_ratio": str(config.min_total_reward_risk_ratio),
        "max_take_profit_targets": config.max_take_profit_targets,
        "max_slippage_bps": config.max_slippage_bps,
        "allowed_exchanges": sorted(config.allowed_exchanges),
        "allowed_symbols": sorted(config.allowed_symbols),
        "blocked_symbols": sorted(config.blocked_symbols),
        "require_fixed_stop_for_pending_trailing": config.require_fixed_stop_for_pending_trailing,
    }


def account_state_to_dict(account_state: AccountState) -> dict[str, Any]:
    return {
        "equity": str(account_state.equity),
        "daily_pnl": str(account_state.daily_pnl),
        "open_notional": str(account_state.open_notional),
        "symbol_open_notional": str(account_state.symbol_open_notional),
        "open_risk_amount": str(account_state.open_risk_amount),
        "consecutive_losses": account_state.consecutive_losses,
    }


def signal_to_dict(signal: CryptoSignal) -> dict[str, Any]:
    return {
        "signal_id": signal.signal_id,
        "source": signal.source,
        "symbol": signal.symbol,
        "side": signal.side,
        "exchange": signal.exchange,
        "market_type": signal.market_type,
        "quote_amount": str(signal.quote_amount) if signal.quote_amount is not None else None,
        "base_amount": str(signal.base_amount) if signal.base_amount is not None else None,
        "risk_amount": str(signal.risk_amount) if signal.risk_amount is not None else None,
        "risk_pct": str(signal.risk_pct) if signal.risk_pct is not None else None,
        "volatility_pct": str(signal.volatility_pct) if signal.volatility_pct is not None else None,
        "price": str(signal.price) if signal.price is not None else None,
        "stop_loss_pct": str(signal.stop_loss_pct) if signal.stop_loss_pct is not None else None,
        "stop_loss_price": str(signal.stop_loss_price) if signal.stop_loss_price is not None else None,
        "take_profit_pct": str(signal.take_profit_pct) if signal.take_profit_pct is not None else None,
        "take_profit_price": str(signal.take_profit_price) if signal.take_profit_price is not None else None,
        "take_profit_targets": [
            {
                "pct": str(target.pct) if target.pct is not None else None,
                "trigger_price": str(target.trigger_price) if target.trigger_price is not None else None,
                "close_pct": str(target.close_pct),
            }
            for target in signal.take_profit_targets
        ],
        "trailing_stop_pct": str(signal.trailing_stop_pct) if signal.trailing_stop_pct is not None else None,
        "trailing_stop_amount": str(signal.trailing_stop_amount) if signal.trailing_stop_amount is not None else None,
        "trailing_stop_price": str(signal.trailing_stop_price) if signal.trailing_stop_price is not None else None,
        "trailing_step_pct": str(signal.trailing_step_pct) if signal.trailing_step_pct is not None else None,
        "trailing_step_amount": str(signal.trailing_step_amount) if signal.trailing_step_amount is not None else None,
        "trailing_activation_pct": str(signal.trailing_activation_pct)
        if signal.trailing_activation_pct is not None
        else None,
        "trailing_activation_price": str(signal.trailing_activation_price)
        if signal.trailing_activation_price is not None
        else None,
        "trail_after_take_profit": signal.trail_after_take_profit,
        "breakeven_trigger_pct": str(signal.breakeven_trigger_pct)
        if signal.breakeven_trigger_pct is not None
        else None,
        "breakeven_after_take_profit": signal.breakeven_after_take_profit,
        "profit_lock_after_take_profit_pct": str(signal.profit_lock_after_take_profit_pct)
        if signal.profit_lock_after_take_profit_pct is not None
        else None,
        "max_hold_marks": signal.max_hold_marks,
        "oca_group": signal.oca_group,
        "leverage": str(signal.leverage),
        "max_slippage_bps": signal.max_slippage_bps,
        "reduce_only": signal.reduce_only,
        "strategy_id": signal.strategy_id,
    }


def risk_decision_to_dict(decision: RiskDecision) -> dict[str, Any]:
    return {
        "approved": decision.approved,
        "reason_codes": decision.reason_codes,
        "order_notional": decimal_to_plain(decision.order_notional) if decision.order_notional is not None else None,
    }


def signal_preview(
    signal: CryptoSignal,
    engine: Any,
    *,
    require_approval: bool,
) -> dict[str, Any]:
    decision = evaluate_signal(signal, engine.risk_config, engine.account_state)
    if engine.halted:
        next_status = "halted"
    elif not decision.approved:
        next_status = "rejected"
    elif require_approval:
        next_status = "approval_required"
    else:
        next_status = "accepted"

    return {
        "signal": signal_to_dict(signal),
        "risk": risk_decision_to_dict(decision),
        "execution": {
            "next_status": next_status,
            "would_place_order": decision.approved and not engine.halted and not require_approval,
            "halted": engine.halted,
            "halt_reason": engine.halt_reason,
            "approval_required": require_approval,
        },
        "bracket_plan": bracket_plan_to_dict(signal, decision, engine.account_state),
        "account": account_state_to_dict(engine.account_state),
    }


def bracket_plan_to_dict(signal: CryptoSignal, decision: RiskDecision, account_state: AccountState) -> dict[str, Any]:
    exits = build_exit_orders(signal)
    exit_side = "sell" if signal.side == "buy" else "buy"
    trailing_starts_armed = (
        (signal.trailing_stop_pct is not None or signal.trailing_stop_amount is not None)
        and signal.trailing_activation_pct is None
        and signal.trailing_activation_price is None
        and not signal.trail_after_take_profit
    )
    trailing_activation_price = planned_trailing_activation_price(signal)
    stop_exit = next((exit_order for exit_order in exits if exit_order.kind == "stop_loss"), None)
    first_target = next((exit_order for exit_order in exits if exit_order.kind == "take_profit"), None)
    estimated_quantity = (
        decision.order_notional / signal.price
        if decision.order_notional is not None and signal.price is not None
        else None
    )
    worst_case = worst_case_loss(signal, decision.order_notional, stop_exit)
    first_target_reward = target_reward(signal, decision.order_notional, first_target)
    total_reward = total_target_reward(signal, decision.order_notional, exits)
    return {
        "entry_side": signal.side,
        "exit_side": exit_side,
        "oca_group": exits[0].oca_group if exits else None,
        "trailing_starts_armed": trailing_starts_armed,
        "trailing_activation_price": decimal_to_plain(trailing_activation_price)
        if trailing_activation_price is not None
        else None,
        "trail_after_take_profit": signal.trail_after_take_profit,
        "breakeven_after_take_profit": signal.breakeven_after_take_profit,
        "profit_lock_after_take_profit_pct": decimal_to_plain(signal.profit_lock_after_take_profit_pct)
        if signal.profit_lock_after_take_profit_pct is not None
        else None,
        "max_hold_marks": signal.max_hold_marks,
        "estimated_notional": decimal_to_plain(decision.order_notional) if decision.order_notional is not None else None,
        "estimated_quantity": decimal_to_plain(estimated_quantity) if estimated_quantity is not None else None,
        "worst_case_loss": decimal_to_plain(worst_case) if worst_case is not None else None,
        "risk_pct_of_equity": decimal_to_plain(worst_case / account_state.equity * Decimal("100"))
        if worst_case is not None and account_state.equity > 0
        else None,
        "first_target_reward": decimal_to_plain(first_target_reward) if first_target_reward is not None else None,
        "first_target_reward_risk_ratio": decimal_to_plain(first_target_reward / worst_case)
        if first_target_reward is not None and worst_case is not None and worst_case > 0
        else None,
        "total_target_reward": decimal_to_plain(total_reward) if total_reward is not None else None,
        "total_target_reward_risk_ratio": decimal_to_plain(total_reward / worst_case)
        if total_reward is not None and worst_case is not None and worst_case > 0
        else None,
        "exits": [
            {
                "kind": exit_order.kind,
                "trigger_price": str(exit_order.trigger_price),
                "close_pct": str(exit_order.close_pct),
                "oca_group": exit_order.oca_group,
                "status": exit_order.status,
                "trailing_step_pct": str(signal.trailing_step_pct)
                if exit_order.kind == "trailing_stop" and signal.trailing_step_pct is not None
                else None,
                "trailing_step_amount": str(signal.trailing_step_amount)
                if exit_order.kind == "trailing_stop" and signal.trailing_step_amount is not None
                else None,
                "trail_after_take_profit": signal.trail_after_take_profit
                if exit_order.kind == "trailing_stop"
                else None,
                "max_hold_marks": signal.max_hold_marks if exit_order.kind == "time_exit" else None,
            }
            for exit_order in exits
        ],
    }


def planned_trailing_activation_price(signal: CryptoSignal) -> Decimal | None:
    if signal.price is None or (signal.trailing_stop_pct is None and signal.trailing_stop_amount is None):
        return None
    if signal.trailing_activation_price is not None:
        return signal.trailing_activation_price
    if signal.trailing_activation_pct is None:
        return None
    direction = Decimal("1") if signal.side == "buy" else Decimal("-1")
    return signal.price * (Decimal("1") + direction * signal.trailing_activation_pct / Decimal("100"))


def worst_case_loss(signal: CryptoSignal, notional: Decimal | None, stop_exit: Any | None) -> Decimal | None:
    if notional is None or signal.price is None or stop_exit is None:
        return None
    stop_distance = (
        signal.price - stop_exit.trigger_price
        if signal.side == "buy"
        else stop_exit.trigger_price - signal.price
    )
    if stop_distance <= 0:
        return None
    return notional * stop_distance / signal.price


def target_reward(signal: CryptoSignal, notional: Decimal | None, target_exit: Any | None) -> Decimal | None:
    if notional is None or signal.price is None or target_exit is None:
        return None
    target_distance = (
        target_exit.trigger_price - signal.price
        if signal.side == "buy"
        else signal.price - target_exit.trigger_price
    )
    if target_distance <= 0:
        return None
    target_notional = notional * target_exit.close_pct / Decimal("100")
    return target_notional * target_distance / signal.price


def total_target_reward(signal: CryptoSignal, notional: Decimal | None, exits: list[Any]) -> Decimal | None:
    rewards = [
        reward
        for exit_order in exits
        if exit_order.kind == "take_profit"
        for reward in [target_reward(signal, notional, exit_order)]
        if reward is not None
    ]
    if not rewards:
        return None
    return sum(rewards, Decimal("0"))


def decimal_to_plain(value: Decimal) -> str:
    return _bracket_decimal_to_plain(value)


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
