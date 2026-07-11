from collections import defaultdict, deque
from threading import Lock
from time import time


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time()
        with self._lock:
            history = self._requests[key]
            while history and history[0] <= now - self.window_seconds:
                history.popleft()
            if len(history) >= self.max_requests:
                return False
            history.append(now)
            return True
