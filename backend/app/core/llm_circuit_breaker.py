from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Awaitable, Callable
import time


def is_transient_llm_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "rate" in msg
        or "429" in msg
        or "throttl" in msg
        or "timeout" in msg
        or "connection" in msg
        or "unavailable" in msg
    )


class CircuitOpenError(RuntimeError):
    """Raised when a circuit is open and request execution is blocked."""


@dataclass
class _CallGrant:
    is_probe: bool


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        failure_window_seconds: float = 60.0,
        open_window_seconds: float = 30.0,
        now_fn: Callable[[], float] | None = None,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.failure_window_seconds = failure_window_seconds
        self.open_window_seconds = open_window_seconds
        self._now = now_fn or time.monotonic
        self._state = "closed"
        self._failures: deque[float] = deque()
        self._reopen_at = 0.0
        self._opened_at_wall: float | None = None
        self._reopen_at_wall: float | None = None
        self._half_open_probe_in_flight = False
        self._lock = Lock()

    async def call(self, coro_factory: Callable[[], Awaitable[Any]]) -> Any:
        grant = self._before_call()
        try:
            result = await coro_factory()
        except Exception as exc:
            self._after_failure(exc, grant)
            raise
        self._after_success(grant)
        return result

    def call_sync(self, fn: Callable[[], Any]) -> Any:
        grant = self._before_call()
        try:
            result = fn()
        except Exception as exc:
            self._after_failure(exc, grant)
            raise
        self._after_success(grant)
        return result

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            data: dict[str, Any] = {
                "state": self._state,
                "failure_count": len(self._failures),
            }
            if self._state == "open":
                if self._opened_at_wall is not None:
                    data["opens_at"] = _iso(self._opened_at_wall)
                if self._reopen_at_wall is not None:
                    data["reopens_at"] = _iso(self._reopen_at_wall)
            return data

    def _before_call(self) -> _CallGrant:
        with self._lock:
            now = self._now()
            if self._state == "open":
                if now < self._reopen_at:
                    raise CircuitOpenError("Circuit is open")
                self._state = "half_open"
                self._half_open_probe_in_flight = False

            if self._state == "half_open":
                if self._half_open_probe_in_flight:
                    raise CircuitOpenError("Circuit is half-open; probe in flight")
                self._half_open_probe_in_flight = True
                return _CallGrant(is_probe=True)

            return _CallGrant(is_probe=False)

    def _after_success(self, grant: _CallGrant) -> None:
        with self._lock:
            self._failures.clear()
            self._state = "closed"
            if grant.is_probe:
                self._half_open_probe_in_flight = False
            self._opened_at_wall = None
            self._reopen_at_wall = None

    def _after_failure(self, exc: Exception, grant: _CallGrant) -> None:
        transient = is_transient_llm_error(exc)
        with self._lock:
            now = self._now()
            if grant.is_probe:
                self._half_open_probe_in_flight = False
                if transient:
                    self._open(now)
                else:
                    self._state = "closed"
                    self._failures.clear()
                return

            if not transient:
                self._failures.clear()
                return

            self._failures.append(now)
            self._prune_failures(now)
            if len(self._failures) >= self.failure_threshold:
                self._open(now)

    def _prune_failures(self, now: float) -> None:
        cutoff = now - self.failure_window_seconds
        while self._failures and self._failures[0] < cutoff:
            self._failures.popleft()

    def _open(self, now: float) -> None:
        self._state = "open"
        self._reopen_at = now + self.open_window_seconds
        self._half_open_probe_in_flight = False
        self._opened_at_wall = time.time()
        self._reopen_at_wall = self._opened_at_wall + self.open_window_seconds


_REGISTRY_LOCK = Lock()
_REGISTRY: dict[str, CircuitBreaker] = {}


def get_breaker(endpoint_key: str) -> CircuitBreaker:
    with _REGISTRY_LOCK:
        breaker = _REGISTRY.get(endpoint_key)
        if breaker is None:
            breaker = CircuitBreaker()
            _REGISTRY[endpoint_key] = breaker
        return breaker


def get_breaker_states() -> dict[str, dict[str, Any]]:
    with _REGISTRY_LOCK:
        items = list(_REGISTRY.items())
    return {key: breaker.snapshot() for key, breaker in items}


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()

