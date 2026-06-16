import pytest

from app.core.llm_circuit_breaker import CircuitBreaker, CircuitOpenError


class _FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.t = start

    def now(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.mark.asyncio
async def test_breaker_starts_closed_and_four_transient_failures_do_not_open():
    clock = _FakeClock()
    breaker = CircuitBreaker(now_fn=clock.now)

    async def _fail():
        raise Exception("connection timeout")

    for _ in range(4):
        with pytest.raises(Exception):
            await breaker.call(_fail)

    state = breaker.snapshot()
    assert state["state"] == "closed"
    assert state["failure_count"] == 4


@pytest.mark.asyncio
async def test_fifth_transient_failure_opens_breaker():
    clock = _FakeClock()
    breaker = CircuitBreaker(now_fn=clock.now)

    async def _fail():
        raise Exception("429 throttled")

    for _ in range(5):
        with pytest.raises(Exception):
            await breaker.call(_fail)

    state = breaker.snapshot()
    assert state["state"] == "open"
    assert "opens_at" in state
    assert "reopens_at" in state


@pytest.mark.asyncio
async def test_open_breaker_rejects_without_invoking_coroutine():
    clock = _FakeClock()
    breaker = CircuitBreaker(now_fn=clock.now)

    async def _fail():
        raise Exception("service unavailable")

    for _ in range(5):
        with pytest.raises(Exception):
            await breaker.call(_fail)

    invoked = False

    async def _should_not_run():
        nonlocal invoked
        invoked = True
        return "ok"

    with pytest.raises(CircuitOpenError):
        await breaker.call(_should_not_run)
    assert invoked is False


@pytest.mark.asyncio
async def test_half_open_probe_success_closes_breaker():
    clock = _FakeClock()
    breaker = CircuitBreaker(now_fn=clock.now)

    async def _fail():
        raise Exception("timeout")

    for _ in range(5):
        with pytest.raises(Exception):
            await breaker.call(_fail)

    clock.advance(30.0)

    async def _success():
        return "ok"

    result = await breaker.call(_success)
    assert result == "ok"
    state = breaker.snapshot()
    assert state["state"] == "closed"
    assert state["failure_count"] == 0


@pytest.mark.asyncio
async def test_half_open_probe_failure_reopens_breaker():
    clock = _FakeClock()
    breaker = CircuitBreaker(now_fn=clock.now)

    async def _fail():
        raise Exception("connection refused")

    for _ in range(5):
        with pytest.raises(Exception):
            await breaker.call(_fail)

    clock.advance(30.0)

    with pytest.raises(Exception):
        await breaker.call(_fail)

    state = breaker.snapshot()
    assert state["state"] == "open"

    with pytest.raises(CircuitOpenError):
        await breaker.call(_fail)


@pytest.mark.asyncio
async def test_non_transient_failure_does_not_increment_failure_counter():
    clock = _FakeClock()
    breaker = CircuitBreaker(now_fn=clock.now)

    async def _non_transient_fail():
        raise Exception("400 bad request: invalid model")

    with pytest.raises(Exception):
        await breaker.call(_non_transient_fail)

    state = breaker.snapshot()
    assert state["state"] == "closed"
    assert state["failure_count"] == 0

