import os

from fastapi import Header, HTTPException

SYNC_ADMIN_TOKEN = os.getenv("NEWS_SYNC_ADMIN_TOKEN", "").strip()


async def verify_sync_token(x_sync_token: str | None = Header(default=None, alias="X-Sync-Token")):
    # 默认拒绝：未配置 NEWS_SYNC_ADMIN_TOKEN 时不允许任何人触发手动同步，
    # 防止接口被匿名滥用（每次同步会抓取外部数据源并写入数据库）
    if not SYNC_ADMIN_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="手动同步未启用：请在 .env 中配置 NEWS_SYNC_ADMIN_TOKEN 后重启服务",
        )
    if not x_sync_token or x_sync_token != SYNC_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Sync token invalid")
