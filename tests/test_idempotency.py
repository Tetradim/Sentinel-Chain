from sentinel_chain.idempotency import InMemoryIdempotencyStore


def test_idempotency_store_claims_key_once_until_expired_clock_advances():
    now = [1000.0]
    store = InMemoryIdempotencyStore(ttl_seconds=30, clock=lambda: now[0])

    assert store.claim("signal-1") is True
    assert store.claim("signal-1") is False

    now[0] = 1031.0

    assert store.claim("signal-1") is True

