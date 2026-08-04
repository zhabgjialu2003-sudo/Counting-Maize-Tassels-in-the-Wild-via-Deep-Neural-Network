"""Bounded local training-job execution for the single-node prototype."""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable


class BoundedJobExecutor:
    def __init__(self, max_workers: int = 1, max_pending: int = 2):
        self.max_workers = max(1, max_workers)
        self.max_pending = max(self.max_workers, max_pending)
        self._capacity = threading.BoundedSemaphore(self.max_pending)
        self._executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="maize-training",
        )

    def submit(self, function: Callable[..., Any], *args, **kwargs) -> Future | None:
        if not self._capacity.acquire(blocking=False):
            return None

        def run():
            try:
                return function(*args, **kwargs)
            finally:
                self._capacity.release()

        try:
            return self._executor.submit(run)
        except Exception:
            self._capacity.release()
            raise

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=True)
