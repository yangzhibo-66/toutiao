import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_conf import get_db
from crud import users
from models.users import User
from schemas.users import (
    UserAuthResponse,
    UserChangePasswordRequest,
    UserInfoResponse,
    UserRequest,
    UserUpdateRequest,
)
from utils import security
from utils.auth import get_current_user
from utils.rate_limit import SlidingWindowLimiter, client_ip
from utils.response import success_response

router = APIRouter(prefix="/api/user", tags=["users"])

# 登录/注册限流：防暴力破解与批量注册（按 IP 计数）
_login_limiter = SlidingWindowLimiter(
    max_events=int(os.getenv("LOGIN_RATE_LIMIT_PER_5MIN", "20")),
    window_seconds=300,
)
_register_limiter = SlidingWindowLimiter(
    max_events=int(os.getenv("REGISTER_RATE_LIMIT_PER_5MIN", "10")),
    window_seconds=300,
)

AVATAR_DIR = Path(__file__).resolve().parent.parent / "uploads" / "avatars"
MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@router.post("/register")
async def register(request: Request, user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    _register_limiter.check(client_ip(request), detail="注册过于频繁，请稍后再试")

    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")

    user = await users.create_user(db, user_data)
    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功", data=response_data)


@router.post("/login")
async def login(request: Request, user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    _login_limiter.check(client_ip(request), detail="登录尝试过于频繁，请稍后再试")

    user = await users.get_user_by_username(db, user_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在，请先注册")
    if not security.verify_password(user_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="密码错误，请重试")

    token = await users.create_token(db, user.id)
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="登录成功", data=response_data)


@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(message="获取用户信息成功", data=UserInfoResponse.model_validate(user))


@router.put("/update")
async def update_user_info(
    user_data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await users.update_user(db, user.username, user_data)
    return success_response(message="更新用户信息成功", data=UserInfoResponse.model_validate(updated_user))


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    extension = ALLOWED_AVATAR_TYPES.get(file.content_type)
    if not extension:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 jpg、png、webp、gif 图片")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传文件不能为空")
    if len(content) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="头像图片不能超过 2MB")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"user_{user.id}_{uuid4().hex}{extension}"
    avatar_file = AVATAR_DIR / filename
    avatar_file.write_bytes(content)

    avatar_path = f"/uploads/avatars/{filename}"
    updated_user = await users.update_user(db, user.username, UserUpdateRequest(avatar=avatar_path))
    return success_response(message="头像上传成功", data=UserInfoResponse.model_validate(updated_user))


@router.put("/password")
async def update_password(
    password_data: UserChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res_change_pwd = await users.change_password(db, user, password_data.old_password, password_data.new_password)
    if not res_change_pwd:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="修改密码失败，请稍后再试")
    return success_response(message="修改密码成功")
