from fastapi import Header, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users


# 整合 根据 Token 查询用户，返回用户
async def get_current_user(
        authorization: str | None = Header(default=None, alias="Authorization"),
        db: AsyncSession = Depends(get_db)
):
    # 未携带 Authorization 头时也统一返回 401，而不是 FastAPI 的 422 参数校验错误
    if not authorization or not authorization.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少认证令牌")

    # Bearer xxxxx
    token = authorization.replace("Bearer ", "")
    user = await users.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌或已经过期的令牌")

    return user


async def get_optional_user(
        authorization: str | None = Header(default=None, alias="Authorization"),
        db: AsyncSession = Depends(get_db)
):
    """可选认证：携带有效 token 时返回用户，缺失或无效时返回 None（不抛 401）。

    用于匿名可用的接口（如 AI 问答），登录用户能获得额外能力（如保存问答记录）。
    """
    if not authorization or not authorization.strip():
        return None

    token = authorization.replace("Bearer ", "")
    return await users.get_user_by_token(db, token)
