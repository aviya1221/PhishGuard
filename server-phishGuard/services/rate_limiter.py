import time
from collections import deque


class RateLimiter:
    """
    In-memory sliding-window rate limiter.

    State lives in the server process, so limits apply per instance
    and reset when the server restarts.
    """

    def __init__(self, max_requests: int, window_seconds: float, max_keys: int = 10_000):
        """
        Args:
            max_requests: Maximum number of requests allowed per key within the window
            window_seconds: Length of the sliding window in seconds
            max_keys: Number of tracked keys that triggers a cleanup of stale entries
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._hits: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        """
        Record a request for the given key if it is within the limit.

        Returns:
            True if the request is allowed, False if the limit was reached
        """
        now = time.monotonic()
        if len(self._hits) > self.max_keys:
            self._purge_stale(now)

        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            return False

        hits.append(now)
        return True

    def _purge_stale(self, now: float) -> None:
        """Drop keys with no requests in the current window so memory doesn't grow with every new client."""
        self._hits = {
            key: hits
            for key, hits in self._hits.items()
            if hits and now - hits[-1] < self.window_seconds
        }
