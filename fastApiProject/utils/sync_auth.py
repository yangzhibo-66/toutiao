import os

from fastapi import Header, HTTPException

SYNC_ADMIN_TOKEN = os.getenv("NEWS_SYNC_ADMIN_TOKEN", "").strip()


async def verify_sync_token(x_sync_token: str | None = Header(default=None, alias="X-Sync-Token")):
    if not SYNC_ADMIN_TOKEN:
        return
    if x_sync_token != SYNC_ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Sync token invalid")
