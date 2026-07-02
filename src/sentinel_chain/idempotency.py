from __future__ import annotations

import time
from collections.abc import Callable


class InMemoryIdempotencyStore:
    """Small process-local idempotency store for duplicate alert suppression."""

    def __init__(self, *, ttl_seconds: int = 300, clock: Callable[[], float] | None = None) -> None:
        self.ttl_seconds = ttl_seconds
        self.clock = clock or time.time
        self._seen: dict[str, float] = {}

    def claim(self, key: str) -> bool:
        self._purge()
        if key in self._seen:
            return False
        self._seen[key] = self.clock()
        return True

    def _purge(self) -> None:
        now = self.clock()
        expired = [key for key, seen_at in self._seen.items() if now - seen_at > self.ttl_seconds]
        for key in expired:
            del self._seen[key]

