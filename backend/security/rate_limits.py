"""Small bounded sliding-window limiter for the single-process prototype."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class RateDecision:
    allowed: bool
    retry_after: int = 0


class InMemoryRateLimiter:
    def __init__(self, max_keys: int = 10_000):
        self._events: dict[str, deque[float]] = {}
        self._max_keys = max(100, max_keys)
        self._lock = threading.RLock()

    def check(
        self,
        scope: str,
        identity: str,
        *,
        limit: int,
        window_seconds: int,
        now: float | None = None,
    ) -> RateDecision:
        current = time.monotonic() if now is None else now
        key = f"{scope}:{identity}"
        cutoff = current - window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(window_seconds - (current - events[0]) + 0.999))
                return RateDecision(False, retry_after)
            events.append(current)
            self._prune(cutoff)
            return RateDecision(True)

    def _prune(self, cutoff: float) -> None:
        if len(self._events) <= self._max_keys:
            return
        stale = [key for key, events in self._events.items() if not events or events[-1] <= cutoff]
        for key in stale:
            self._events.pop(key, None)
        while len(self._events) > self._max_keys:
            self._events.pop(next(iter(self._events)))

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
