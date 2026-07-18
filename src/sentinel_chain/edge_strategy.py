"""Edge-authorized strategy lifecycle for Sentinel Chain.

New exposure can be required to obtain an ``edge.strategy.authorization.v1``
trade card.  Risk-reducing signals remain locally executable so an unavailable
strategist can never prevent a protective exit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
import math
import os
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .signals import CryptoSignal


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _decimal(value: Any) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except Exception:
        return None
    return number if number.is_finite() and number > 0 else None


def _float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


class EdgeAuthorizationStore:
    def __init__(self, path: Path | None = None) -> None:
        configured = os.getenv("CHAIN_EDGE_AUTHORIZATION_FILE", "").strip()
        self.path = path or (Path(configured) if configured else Path("data") / "edge-authorizations.json")
        self._lock = Lock()
        self._cards: dict[str, dict[str, Any]] = {}
        self._load()

    def record(self, authorization: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(authorization, dict):
            raise ValueError("authorization must be an object")
        if authorization.get("contract_version") != "edge.strategy.authorization.v1":
            raise ValueError("unsupported Edge authorization contract")
        if not bool(authorization.get("authorized")):
            raise ValueError("Edge rejected the strategy proposal")
        if str(authorization.get("target_bot") or "").strip().lower() != "sentinel-chain":
            raise ValueError("authorization is not assigned to sentinel-chain")
        card = authorization.get("trade_card") if isinstance(authorization.get("trade_card"), dict) else {}
        card_id = str(card.get("card_id") or "").strip()
        if not card_id:
            raise ValueError("authorized response is missing trade_card.card_id")
        with self._lock:
            self._cards[card_id] = dict(authorization)
            self._save()
        return authorization

    def latest_for_symbol(self, symbol: str) -> dict[str, Any] | None:
        symbol = str(symbol or "").upper()
        with self._lock:
            values = list(self._cards.values())
        candidates = []
        for authorization in values:
            card = authorization.get("trade_card") if isinstance(authorization.get("trade_card"), dict) else {}
            if str(card.get("symbol") or authorization.get("symbol") or "").upper() != symbol:
                continue
            if self.validation_reasons(authorization, symbol=symbol, side=None, requested_notional=None):
                continue
            candidates.append(authorization)
        candidates.sort(key=lambda item: str((item.get("trade_card") or {}).get("updated_at") or item.get("evaluated_at") or ""), reverse=True)
        return dict(candidates[0]) if candidates else None

    def get(self, card_id: str) -> dict[str, Any] | None:
        with self._lock:
            value = self._cards.get(str(card_id or ""))
            return dict(value) if value else None

    def validation_reasons(
        self,
        authorization: dict[str, Any],
        *,
        symbol: str,
        side: str | None,
        requested_notional: Decimal | None,
    ) -> list[str]:
        reasons: list[str] = []
        if authorization.get("contract_version") != "edge.strategy.authorization.v1":
            reasons.append("edge_authorization_contract_invalid")
        if not bool(authorization.get("authorized")):
            reasons.append("edge_authorization_rejected")
        if str(authorization.get("target_bot") or "").lower() != "sentinel-chain":
            reasons.append("edge_authorization_wrong_bot")
        card = authorization.get("trade_card") if isinstance(authorization.get("trade_card"), dict) else {}
        if str(card.get("symbol") or authorization.get("symbol") or "").upper() != str(symbol).upper():
            reasons.append("edge_authorization_symbol_mismatch")
        state = str(card.get("state") or "").lower()
        if state not in {"armed", "entering", "active", "reducing", "exiting"}:
            reasons.append("edge_trade_card_not_active")
        expiry = _parse_time(card.get("expires_at"))
        if expiry is not None and expiry <= _now():
            reasons.append("edge_trade_card_expired")
        direction = str(card.get("direction") or "long").lower()
        if side == "buy" and direction == "short":
            reasons.append("edge_authorization_direction_mismatch")
        if side == "sell" and direction == "long":
            reasons.append("edge_authorization_direction_mismatch")
        target_notional = _decimal(card.get("target_notional") or authorization.get("target_notional"))
        if requested_notional is not None and target_notional is not None:
            tolerance = Decimal(str(os.getenv("CHAIN_EDGE_NOTIONAL_TOLERANCE_PCT", "2"))) / Decimal("100")
            if requested_notional > target_notional * (Decimal("1") + max(Decimal("0"), tolerance)):
                reasons.append("edge_target_notional_exceeded")
        stop_owner = (card.get("metadata") or {}).get("stop_owner") if isinstance(card.get("metadata"), dict) else None
        if isinstance(stop_owner, dict) and stop_owner.get("position_id") != card.get("position_id"):
            reasons.append("edge_stop_owner_mismatch")
        return reasons

    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return
        if isinstance(raw, dict):
            self._cards = {str(key): value for key, value in raw.items() if isinstance(value, dict)}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(self._cards, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)


authorizations = EdgeAuthorizationStore()


def _edge_request(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = os.getenv("EDGE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    secret = os.getenv("EDGE_OPERATOR_ACTION_SECRET", "").strip()
    if not secret:
        raise RuntimeError("EDGE_OPERATOR_ACTION_SECRET is not configured")
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        f"{base_url}{path}",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "X-Edge-Operator-Secret": secret},
    )
    timeout = max(0.5, float(os.getenv("CHAIN_EDGE_TIMEOUT_SECONDS", "4") or 4))
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Edge returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Edge is unavailable: {exc.reason}") from exc


def _signal_notional(signal: CryptoSignal) -> Decimal | None:
    if signal.quote_amount is not None:
        return signal.quote_amount
    if signal.base_amount is not None and signal.price is not None:
        return signal.base_amount * signal.price
    return None


def build_proposal(signal: CryptoSignal) -> dict[str, Any]:
    price = signal.price
    stop = signal.stop_loss_price
    first_target = signal.take_profit_price
    if first_target is None and signal.take_profit_targets:
        first_target = signal.take_profit_targets[0].trigger_price
    risk_pct = Decimal("0")
    reward_pct = Decimal("0")
    if price and stop:
        risk_pct = abs(price - stop) / price * Decimal("100")
    elif signal.stop_loss_pct:
        risk_pct = signal.stop_loss_pct
    if price and first_target:
        reward_pct = abs(first_target - price) / price * Decimal("100")
    elif signal.take_profit_pct:
        reward_pct = signal.take_profit_pct
    raw = signal.raw_payload if isinstance(signal.raw_payload, dict) else {}
    confidence = max(0.0, min(1.0, _float(raw.get("confidence"), 0.80)))
    regime = str(raw.get("regime") or "unknown").strip().lower()
    direction = "short" if signal.side == "sell" and not signal.reduce_only else "long"
    targets = [str(target.trigger_price) for target in signal.take_profit_targets if target.trigger_price is not None]
    if not targets and first_target is not None:
        targets = [str(first_target)]
    return {
        "contract_version": "edge.strategy.proposal.v1",
        "proposal_id": f"sentinel-chain:{signal.signal_id}",
        "correlation_id": signal.signal_id,
        "source_bot": "sentinel-chain",
        "target_bot": "sentinel-chain",
        "symbol": signal.symbol,
        "strategy": signal.strategy_id or "crypto_signal",
        "direction": direction,
        "confidence": confidence,
        "regime": regime,
        "expected_reward_pct": float(reward_pct),
        "expected_risk_pct": float(risk_pct),
        "estimated_cost_pct": max(0.0, _float(raw.get("estimated_cost_pct"), signal.max_slippage_bps / 100.0)),
        "entry_price": float(price) if price is not None else None,
        "stop_price": float(stop) if stop is not None else None,
        "targets": [float(value) for value in targets],
        "maximum_entry_price": _float(raw.get("maximum_entry_price")) or None,
        "invalidation": str(raw.get("invalidation") or "crypto strategy thesis invalidated"),
        "requested_notional": float(_signal_notional(signal)) if _signal_notional(signal) is not None else None,
    }


def ensure_authorized(signal: CryptoSignal) -> list[str]:
    if signal.reduce_only:
        return []
    required = os.getenv("CHAIN_REQUIRE_EDGE_AUTHORIZATION", "true").strip().lower() in {"1", "true", "yes", "on"}
    if not required:
        return []
    raw = signal.raw_payload if isinstance(signal.raw_payload, dict) else {}
    card_id = str(raw.get("edge_card_id") or raw.get("card_id") or "").strip()
    authorization = authorizations.get(card_id) if card_id else authorizations.latest_for_symbol(signal.symbol)
    if authorization is None:
        try:
            response = _edge_request("/bus/profitability/opportunities", build_proposal(signal))
            authorization = response.get("authorization") if isinstance(response.get("authorization"), dict) else None
            if authorization is None:
                return ["edge_authorization_missing"]
            authorizations.record(authorization)
        except Exception:
            return ["edge_authorization_unavailable"]
    requested_notional = _signal_notional(signal)
    return authorizations.validation_reasons(
        authorization,
        symbol=signal.symbol,
        side=signal.side,
        requested_notional=requested_notional,
    )


def receive_authorization_event(event: Any) -> None:
    if str(getattr(event, "event_type", "")) != "edge.strategy.authorization":
        return
    targets = list(getattr(event, "target_bots", []) or [])
    if targets and "sentinel-chain" not in targets:
        return
    payload = getattr(event, "payload", None)
    if isinstance(payload, dict) and payload.get("authorized"):
        try:
            authorizations.record(payload)
        except ValueError:
            return


def register_with_event_bus() -> None:
    from .bot_event_bus import register_event_listener

    register_event_listener(receive_authorization_event)


def record_signal_result(signal: CryptoSignal, result: Any) -> None:
    if signal.reduce_only:
        return
    authorization = authorizations.latest_for_symbol(signal.symbol)
    if not authorization:
        return
    card = authorization.get("trade_card") if isinstance(authorization.get("trade_card"), dict) else {}
    payload = result.to_dict() if hasattr(result, "to_dict") else dict(result) if isinstance(result, dict) else {"result": str(result)}
    feedback = {
        "contract_version": "edge.strategy.feedback.v1",
        "feedback_id": f"sentinel-chain:{signal.signal_id}:{payload.get('status', 'unknown')}",
        "card_id": card.get("card_id"),
        "position_id": card.get("position_id"),
        "symbol": signal.symbol,
        "source_bot": "sentinel-chain",
        "action": "entry" if payload.get("status") in {"accepted", "filled", "approval_required"} else "rejected",
        "feedback": payload,
        "metadata": {"signal_id": signal.signal_id, "strategy_id": signal.strategy_id},
    }

    def deliver() -> None:
        try:
            _edge_request("/bus/profitability/feedback", feedback)
        except Exception:
            return

    Thread(target=deliver, name=f"chain-edge-feedback-{signal.signal_id}", daemon=True).start()
