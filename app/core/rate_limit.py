from collections import defaultdict, deque
from time import time

from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.bucket: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = time()
        queue = self.bucket[key]
        while queue and now - queue[0] > self.window_seconds:
            queue.popleft()
        if len(queue) >= self.limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        queue.append(now)
