import fnmatch
import json
import os
import time
from typing import Any

import redis.asyncio as redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Redis 连接失败后的熔断间隔（秒）：期间直接走内存缓存，避免每个请求都等待连接超时
REDIS_RETRY_INTERVAL = float(os.getenv("REDIS_RETRY_INTERVAL", "30"))

redis_client = redis.Redis(
    host=REDIS_HOST,  # Redis 服务器的主机地址
    port=REDIS_PORT,  # Redis 端口号
    db=REDIS_DB,  # Redis 数据库编号，0~15
    decode_responses=True,  # 是否将字节数据解码为字符串
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
)

# 进程内存兜底缓存：{key: (value_str, expires_at_monotonic)}
# Redis 不可用时自动降级到这里，单机无 Redis 部署也能获得缓存加速
_memory_cache: dict[str, tuple[str, float]] = {}
_redis_down_until = 0.0


def _memory_get(key: str) -> str | None:
    entry = _memory_cache.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if expires_at <= time.monotonic():
        _memory_cache.pop(key, None)
        return None
    return value


def _memory_set(key: str, value: str, expire: int) -> None:
    # 简单的容量上限，防止极端情况下内存无限增长
    if len(_memory_cache) >= 5000:
        now = time.monotonic()
        for stale_key in [k for k, (_, exp) in _memory_cache.items() if exp <= now]:
            _memory_cache.pop(stale_key, None)
    _memory_cache[key] = (value, time.monotonic() + expire)


def _redis_available() -> bool:
    return time.monotonic() >= _redis_down_until


def _mark_redis_down() -> None:
    global _redis_down_until
    _redis_down_until = time.monotonic() + REDIS_RETRY_INTERVAL


# 读取：字符串。Redis 优先，不可用时读内存兜底
async def get_cache(key: str):
    if _redis_available():
        try:
            value = await redis_client.get(key)
            if value is not None:
                return value
        except Exception as e:
            print(f"获取缓存失败（Redis，降级内存）：{e}")
            _mark_redis_down()
    return _memory_get(key)


# 读取：列表或字典（JSON 反序列化）
async def get_json_cache(key: str):
    data = await get_cache(key)
    if not data:
        return None
    try:
        return json.loads(data)
    except (TypeError, ValueError):
        return None


# 设置缓存 setex(key, expire, value)：Redis 与内存同时写，读端 Redis 优先
async def set_cache(key: str, value: Any, expire: int = 3600):
    if isinstance(value, (dict, list)):
        try:
            value = json.dumps(value, ensure_ascii=False, default=str)  # 中文正常保存
        except (TypeError, ValueError):
            # 序列化失败不能影响业务请求，只是放弃这次缓存
            return False
    _memory_set(key, str(value), expire)

    if not _redis_available():
        return False
    try:
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"设置缓存失败（Redis，降级内存）：{e}")
        _mark_redis_down()
        return False


async def delete_cache_keys(*keys: str) -> None:
    """精确删除若干缓存 key（Redis 与内存同步删除）。"""
    for key in keys:
        _memory_cache.pop(key, None)
    if not keys or not _redis_available():
        return
    try:
        await redis_client.delete(*keys)
    except Exception:
        _mark_redis_down()


async def delete_cache_pattern(pattern: str) -> int:
    """按通配符删除缓存（如 news_list:*），返回删除数量。"""
    removed = 0
    for key in [k for k in _memory_cache if fnmatch.fnmatchcase(k, pattern)]:
        _memory_cache.pop(key, None)
        removed += 1

    if not _redis_available():
        return removed
    try:
        deleted = 0
        async for key in redis_client.scan_iter(match=pattern, count=200):
            deleted += await redis_client.delete(key)
        return deleted
    except Exception:
        _mark_redis_down()
        return removed
