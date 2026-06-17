from __future__ import annotations

from .execution import ExecutionResult, PaperExchange
from .idempotency import InMemoryIdempotencyStore
from .risk import AccountState, RiskConfig, evaluate_signal
from .signals import CryptoSignal


class TradingEngine:
    """Coordinates validation, risk, duplicate detection, and paper execution."""

    def __init__(
        self,
        *,
        exchange: PaperExchange | None = None,
        risk_config: RiskConfig | None = None,
        account_state: AccountState | None = None,
        idempotency: InMemoryIdempotencyStore | None = None,
    ) -> None:
        self.exchange = exchange or PaperExchange()
        self.risk_config = risk_config or RiskConfig()
        self.account_state = account_state or AccountState()
        self.idempotency = idempotency or InMemoryIdempotencyStore()

    def process_signal(self, signal: CryptoSignal) -> ExecutionResult:
        decision = evaluate_signal(signal, self.risk_config, self.account_state)
        if not decision.approved:
            return ExecutionResult(status="rejected", decision=decision, reason="risk_rejected")

        if not self.idempotency.claim(signal.signal_id):
            return ExecutionResult(status="duplicate", decision=decision, reason="duplicate_signal")

        order = self.exchange.submit(signal, decision)
        return ExecutionResult(status="accepted", decision=decision, order=order)

