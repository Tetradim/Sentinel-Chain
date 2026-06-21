from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StrategyPreset:
    name: str
    description: str
    entry_logic: tuple[str, ...]
    signal_defaults: dict[str, Any]
    suggested_bracket_template: str
    backtest_defaults: dict[str, Any]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "entry_logic": list(self.entry_logic),
            "signal_defaults": deepcopy(self.signal_defaults),
            "suggested_bracket_template": self.suggested_bracket_template,
            "backtest_defaults": deepcopy(self.backtest_defaults),
            "notes": list(self.notes),
        }


STRATEGY_PRESETS: dict[str, StrategyPreset] = {
    "momentum_breakout": StrategyPreset(
        name="momentum_breakout",
        description="Long continuation setup after price clears a recent range high with volume confirmation.",
        entry_logic=(
            "Use only after an external scanner or operator confirms a breakout level.",
            "Prefer BTC, ETH, SOL, and liquid USDT pairs where spread/slippage are reviewable.",
            "Reject if the move is already extended beyond the configured volatility guard.",
        ),
        signal_defaults={
            "side": "buy",
            "market_type": "swap",
            "strategy_id": "momentum_breakout",
            "max_slippage_bps": 100,
        },
        suggested_bracket_template="activation_trailer",
        backtest_defaults={
            "lookback": "7d",
            "interval": "1h",
            "close_final_positions": True,
        },
        notes=(
            "Pairs naturally with activation-gated trailing exits.",
            "The preset does not generate signals; it documents and normalizes operator-reviewed entries.",
        ),
    ),
    "dip_reclaim": StrategyPreset(
        name="dip_reclaim",
        description="Long mean-reversion setup after a selloff reclaims a watched support or moving-average area.",
        entry_logic=(
            "Use after a reclaim is visible on the operator's chosen timeframe.",
            "Prefer smaller fixed brackets while testing because failed reclaims can reverse quickly.",
            "Review recent drawdown and same-candle stop/target ambiguity before sizing up.",
        ),
        signal_defaults={
            "side": "buy",
            "market_type": "swap",
            "strategy_id": "dip_reclaim",
            "max_slippage_bps": 100,
        },
        suggested_bracket_template="fixed_bracket",
        backtest_defaults={
            "lookback": "7d",
            "interval": "1h",
            "close_final_positions": True,
        },
    ),
    "range_reversion_short": StrategyPreset(
        name="range_reversion_short",
        description="Short setup after a failed range breakout or rejection from resistance.",
        entry_logic=(
            "Use only where shorting is supported in the selected paper/backtest venue model.",
            "Prefer liquid pairs and conservative slippage assumptions.",
            "Check funding and borrow constraints outside Auto-Crypto before any live mapping.",
        ),
        signal_defaults={
            "side": "sell",
            "market_type": "swap",
            "strategy_id": "range_reversion_short",
            "max_slippage_bps": 100,
        },
        suggested_bracket_template="fixed_bracket",
        backtest_defaults={
            "lookback": "7d",
            "interval": "1h",
            "close_final_positions": True,
        },
    ),
}


def list_strategy_presets() -> list[dict[str, Any]]:
    return [preset.to_dict() for preset in STRATEGY_PRESETS.values()]


def get_strategy_preset(name: str) -> StrategyPreset:
    normalized = name.strip().lower()
    try:
        return STRATEGY_PRESETS[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown strategy preset: {name}") from exc


def apply_strategy_preset(
    signal_payload: dict[str, Any],
    preset_name: str,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(signal_payload, dict):
        raise ValueError("signal must be an object")
    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("overrides must be an object")

    preset = get_strategy_preset(preset_name)
    merged = deepcopy(preset.signal_defaults)
    merged.update(deepcopy(signal_payload))
    if overrides:
        merged.update(deepcopy(overrides))
    merged["strategy_preset"] = preset.name
    return merged
