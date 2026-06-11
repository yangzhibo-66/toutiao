import re

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import Category, News
from schemas.base import NewsItemBase
from schemas.news import RelatedNewsResponse

TITLE_SUFFIX_SPLIT_RE = re.compile(r"\s*[-|_]\s*")
TITLE_TRAILING_SITE_RE = re.compile(r"(?:_[^_]+){1,3}$")
TITLE_WHITESPACE_RE = re.compile(r"\s+")


def normalize_news_title(value: str | None) -> str:
    title = (value or "").strip()
    if not title:
        return ""

    title = TITLE_TRAILING_SITE_RE.sub("", title).strip()
    title = TITLE_SUFFIX_SPLIT_RE.split(title, 1)[0].strip()
    title = TITLE_WHITESPACE_RE.sub("", title)
    return title.lower()


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    stmt = select(Category).order_by(Category.sort_order.asc(), Category.id.asc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def _load_latest_news_rows(db: AsyncSession, category_id: int) -> list[dict]:
    stmt = (
        select(
            News.id,
            News.title,
            News.description,
            News.image,
            News.source_url,
            News.author,
            News.category_id,
            News.views,
            News.publish_time,
        )
        .where(News.category_id == category_id)
        .order_by(News.publish_time.desc(), News.id.desc())
    )
    result = await db.execute(stmt)
    return [dict(row._mapping) for row in result.all()]


def _dedupe_news_rows(rows: list[dict]) -> list[dict]:
    deduped_rows: list[dict] = []
    seen_titles: set[str] = set()

    for item in rows:
        normalized_title = normalize_news_title(item.get("title"))
        dedupe_key = normalized_title or str(item.get("id"))
        if dedupe_key in seen_titles:
            continue
        seen_titles.add(dedupe_key)
        deduped_rows.append(item)

    return deduped_rows


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    rows = await _load_latest_news_rows(db, category_id)
    deduped_rows = _dedupe_news_rows(rows)
    page_rows = deduped_rows[skip: skip + limit]
    return [
        NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False)
        for item in page_rows
    ]


async def get_news_count(db: AsyncSession, category_id: int):
    rows = await _load_latest_news_rows(db, category_id)
    return len(_dedupe_news_rows(rows))


async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    stmt = (
        select(News)
        .where(
            News.category_id == category_id,
            News.id != news_id,
        )
        .order_by(News.views.desc(), News.publish_time.desc())
    )
    result = await db.execute(stmt)
    related_news = result.scalars().all()

    deduped_rows: list[News] = []
    seen_titles: set[str] = set()
    for item in related_news:
        dedupe_key = normalize_news_title(item.title) or str(item.id)
        if dedupe_key in seen_titles:
            continue
        seen_titles.add(dedupe_key)
        deduped_rows.append(item)
        if len(deduped_rows) >= limit:
            break

    return [
        RelatedNewsResponse.model_validate(news_detail).model_dump(by_alias=False, mode="json")
        for news_detail in deduped_rows
    ]
