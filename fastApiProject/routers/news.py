from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from cache.news_cache import (
    cache_news_detail,
    get_cache_news_hot,
    get_cache_news_list,
    get_cached_categories,
    get_cached_news_detail,
    invalidate_news_cache,
    set_cache_categories,
    set_cache_news_hot,
    set_cache_news_list,
)
from config.db_conf import get_db
from crud import news
from models.users import User
from schemas.base import NewsItemBase
from schemas.news import NewsCreateRequest
from services.news_detail_enrichment import maybe_enrich_news_detail
from services.news_sync import get_sync_status, run_sync_once
from utils.auth import get_current_user
from utils.sync_auth import verify_sync_token

router = APIRouter(prefix="/api/news", tags=["news"])

NEWS_IMAGE_DIR = Path(__file__).resolve().parent.parent / "uploads" / "news"
MAX_NEWS_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_NEWS_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _serialize_news_item(news_item):
    return NewsItemBase.model_validate(news_item).model_dump(mode="json", by_alias=False)


def _serialize_owned_news_item(news_item):
    data = _serialize_news_item(news_item)
    data["content"] = news_item.content
    return data


def _build_news_payload(
    title: str,
    content: str,
    category_id: int,
    description: str | None,
    image_url: str | None,
    author: str | None,
    username: str,
) -> NewsCreateRequest:
    title_text = title.strip()
    content_text = content.strip()
    description_text = (description or "").strip()
    image_url_text = (image_url or "").strip()
    author_text = (author or "").strip()

    if len(title_text) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新闻标题至少需要 2 个字符")
    if len(content_text) < 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新闻正文至少需要 10 个字符")
    if len(description_text) > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新闻简介不能超过 500 个字符")
    if len(image_url_text) > 255:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="图片链接不能超过 255 个字符")

    return NewsCreateRequest(
        title=title_text,
        description=description_text or None,
        content=content_text,
        image=image_url_text or None,
        author=author_text or username,
        categoryId=category_id,
    )


async def _save_news_image(file: UploadFile | None) -> str | None:
    if not file or not file.filename:
        return None

    extension = ALLOWED_NEWS_IMAGE_TYPES.get(file.content_type)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 jpg、png、webp、gif 图片",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传图片不能为空")
    if len(content) > MAX_NEWS_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="新闻封面不能超过 5MB")

    NEWS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"news_{uuid4().hex}{extension}"
    (NEWS_IMAGE_DIR / filename).write_bytes(content)
    return f"/uploads/news/{filename}"


@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    cached_categories = await get_cached_categories()
    if cached_categories:
        return {
            "code": 200,
            "message": "获取新闻分类成功",
            "data": cached_categories,
        }

    categories = await news.get_categories(db, skip, limit)
    data = [{"id": item.id, "name": item.name} for item in categories]
    await set_cache_categories(data)
    return {
        "code": 200,
        "message": "获取新闻分类成功",
        "data": data,
    }


@router.get("/list")
async def get_news_list(
    category_id: int = Query(..., alias="categoryId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, alias="pageSize", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    cached_payload = await get_cache_news_list(category_id, page, page_size)
    if cached_payload:
        return {
            "code": 200,
            "message": "获取新闻列表成功",
            "data": cached_payload,
        }

    offset = (page - 1) * page_size
    news_list = await news.get_news_list(db, category_id, offset, page_size)
    total = await news.get_news_count(db, category_id)
    has_more = (offset + len(news_list)) < total
    payload = {
        "list": news_list,
        "total": total,
        "hasMore": has_more,
    }
    await set_cache_news_list(category_id, page, page_size, payload)
    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": payload,
    }


@router.get("/hot")
async def get_news_hot(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, alias="pageSize", ge=1, le=50),
    category_id: int | None = Query(None, alias="categoryId"),
    db: AsyncSession = Depends(get_db),
):
    """全库（或指定分类）热榜：按阅读量排序，聚合在数据库完成。"""
    cached_payload = await get_cache_news_hot(category_id, page, page_size)
    if cached_payload:
        return {
            "code": 200,
            "message": "获取新闻热榜成功",
            "data": cached_payload,
        }

    offset = (page - 1) * page_size
    items = await news.get_hot_news(db, category_id, offset, page_size)
    total = await news.get_hot_news_count(db, category_id)
    payload = {
        "list": [_serialize_news_item(item) for item in items],
        "total": total,
        "hasMore": offset + len(items) < total,
    }
    await set_cache_news_hot(category_id, page, page_size, payload)
    return {
        "code": 200,
        "message": "获取新闻热榜成功",
        "data": payload,
    }


@router.get("/search")
async def search_news(
    keyword: str = Query(..., alias="keyword", min_length=1, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, alias="pageSize", ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """站内搜索：按标题/简介关键词检索，发布时间倒序分页。"""
    offset = (page - 1) * page_size
    items = await news.search_news(db, keyword, offset, page_size)
    total = await news.search_news_count(db, keyword)
    return {
        "code": 200,
        "message": "搜索新闻成功",
        "data": {
            "list": [_serialize_news_item(item) for item in items],
            "total": total,
            "hasMore": offset + len(items) < total,
        },
    }


@router.get("/detail")
async def get_news_detail(news_id: int = Query(..., alias="id"), db: AsyncSession = Depends(get_db)):
    cached_detail = await get_cached_news_detail(news_id)
    if cached_detail:
        # 缓存命中也要累计浏览量，只是响应中的 views 允许短暂滞后（缓存 5 分钟）
        await news.increase_news_views(db, news_id)
        return {
            "code": 200,
            "message": "success",
            "data": cached_detail,
        }

    news_detail = await news.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")

    news_detail = await maybe_enrich_news_detail(db, news_detail)

    views_res = await news.increase_news_views(db, news_detail.id)
    if not views_res:
        raise HTTPException(status_code=404, detail="新闻不存在")

    related_news = await news.get_related_news(db, news_detail.id, news_detail.category_id)

    data = {
        "id": news_detail.id,
        "title": news_detail.title,
        "description": news_detail.description,
        "content": news_detail.content,
        "image": news_detail.image,
        "sourceUrl": news_detail.source_url,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
        "relatedNews": related_news,
    }
    # 先转成 JSON 安全类型（如 datetime -> ISO 字符串），缓存写入和响应共用这一份
    data = jsonable_encoder(data)
    await cache_news_detail(news_id, data)
    return {
        "code": 200,
        "message": "success",
        "data": data,
    }


@router.post("/upload")
async def upload_news(
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(..., alias="categoryId"),
    description: str | None = Form(None),
    author: str | None = Form(None),
    image_url: str | None = Form(None, alias="imageUrl"),
    image: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    news_payload = _build_news_payload(title, content, category_id, description, image_url, author, user.username)
    category = await news.get_category_by_id(db, news_payload.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新闻分类不存在")

    uploaded_image = await _save_news_image(image)
    created_news = await news.create_news(
        db,
        {
            "title": news_payload.title,
            "description": news_payload.description or news_payload.content[:120],
            "content": news_payload.content,
            "image": uploaded_image or news_payload.image,
            "author": news_payload.author,
            "user_id": user.id,
            "category_id": news_payload.category_id,
            "views": 0,
        },
    )
    await invalidate_news_cache()

    return {
        "code": 200,
        "message": "新闻发布成功",
        "data": _serialize_news_item(created_news),
    }


@router.get("/mine")
async def get_my_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    items = await news.get_user_news_list(db, user.id, offset, page_size)
    total = await news.get_user_news_count(db, user.id)
    return {
        "code": 200,
        "message": "获取已发布新闻成功",
        "data": {
            "list": [_serialize_owned_news_item(item) for item in items],
            "total": total,
            "hasMore": offset + len(items) < total,
        },
    }


@router.get("/mine/{news_id}")
async def get_my_news_detail(
    news_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned_news = await news.get_user_news_detail(db, news_id, user.id)
    if not owned_news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="新闻不存在或无权查看")

    return {
        "code": 200,
        "message": "获取已发布新闻详情成功",
        "data": _serialize_owned_news_item(owned_news),
    }


@router.put("/{news_id}")
async def update_my_news(
    news_id: int,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(..., alias="categoryId"),
    description: str | None = Form(None),
    author: str | None = Form(None),
    image_url: str | None = Form(None, alias="imageUrl"),
    image: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned_news = await news.get_user_news_detail(db, news_id, user.id)
    if not owned_news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="新闻不存在或无权修改")

    news_payload = _build_news_payload(title, content, category_id, description, image_url, author, user.username)
    category = await news.get_category_by_id(db, news_payload.category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新闻分类不存在")

    uploaded_image = await _save_news_image(image)
    updated_news = await news.update_user_news(
        db,
        owned_news,
        {
            "title": news_payload.title,
            "description": news_payload.description or news_payload.content[:120],
            "content": news_payload.content,
            "image": uploaded_image or news_payload.image,
            "author": news_payload.author,
            "category_id": news_payload.category_id,
        },
    )
    await invalidate_news_cache()

    return {
        "code": 200,
        "message": "新闻修改成功",
        "data": _serialize_owned_news_item(updated_news),
    }


@router.delete("/{news_id}")
async def delete_my_news(
    news_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owned_news = await news.get_user_news_detail(db, news_id, user.id)
    if not owned_news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="新闻不存在或无权删除")

    await news.delete_user_news(db, owned_news)
    await invalidate_news_cache()
    return {
        "code": 200,
        "message": "新闻删除成功",
        "data": {"id": news_id},
    }


@router.post("/sync")
async def sync_latest_news(_: None = Depends(verify_sync_token)):
    result = await run_sync_once()
    await invalidate_news_cache()
    return {
        "code": 200,
        "message": "新闻同步成功",
        "data": result,
    }


@router.get("/sync/status")
async def get_news_sync_status():
    return {
        "code": 200,
        "message": "获取同步状态成功",
        "data": get_sync_status(),
    }
