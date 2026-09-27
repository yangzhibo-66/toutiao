"""进程内滑动窗口限流器。

用于保护登录/注册（防暴力破解）和 AI 问答（防刷额度）等接口。
单实例部署下无需引入 Redis 依赖；多实例部署时可替换为集中式实现。
"""

import time
from collections import deque

from fastapi import HTTPException, Request

# 最多跟踪的 key 数量，超过时清理长期不活跃的，防止内存无限增长
_MAX_BUCKETS = 10000


def client_ip(request: Request) -> str:
    """取客户端 IP：优先 X-Forwarded-For 首段（反向代理场景），否则取连接对端。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._buckets: dict[str, deque[float]] = {}

    def check(self, key: str, detail: str = "请求过于频繁，请稍后再试") -> None:
        """记录一次事件；超出窗口内限额时抛出 429。"""
        now = time.monotonic()
        bucket = self._buckets.setdefault(key, deque())
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.max_events:
            raise HTTPException(status_code=429, detail=detail)
        bucket.append(now)

        if len(self._buckets) > _MAX_BUCKETS:
            stale = [k for k, b in self._buckets.items() if not b or now - b[-1] > self.window_seconds]
            for k in stale:
                self._buckets.pop(k, None)
