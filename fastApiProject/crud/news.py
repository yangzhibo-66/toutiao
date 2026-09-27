import re

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.history import History
from models.news import Category, News
from schemas.base import NewsItemBase
from schemas.news import RelatedNewsResponse

TITLE_SUFFIX_SPLIT_RE = re.compile(r"\s*[-|_]\s*")
TITLE_TRAILING_SITE_RE = re.compile(r"(?:_[^_]+){1,3}$")
TITLE_WHITESPACE_RE = re.compile(r"\s+")

# 相关新闻最多扫描的候选行数，避免大分类下全量加载
RELATED_SCAN_LIMIT = 100


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


async def get_category_by_id(db: AsyncSession, category_id: int):
    stmt = select(Category).where(Category.id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_news(db: AsyncSession, news_data: dict):
    news_item = News(**news_data)
    db.add(news_item)
    await db.flush()
    await db.refresh(news_item)
    return news_item


async def get_user_news_list(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    stmt = (
        select(News)
        .where(News.user_id == user_id)
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_user_news_count(db: AsyncSession, user_id: int):
    stmt = select(func.count()).select_from(News).where(News.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_user_news_detail(db: AsyncSession, news_id: int, user_id: int):
    stmt = select(News).where(News.id == news_id, News.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_news(db: AsyncSession, news_item: News, news_data: dict):
    for key, value in news_data.items():
        setattr(news_item, key, value)
    db.add(news_item)
    await db.flush()
    await db.refresh(news_item)
    return news_item


async def delete_user_news(db: AsyncSession, news_item: News):
    await db.execute(delete(Favorite).where(Favorite.news_id == news_item.id))
    await db.execute(delete(History).where(History.news_id == news_item.id))
    await db.delete(news_item)
    await db.flush()
    return True


async def _load_latest_news_ids(db: AsyncSession, category_id: int) -> list[int]:
    """按发布时间倒序取该分类的 id + title 轻量列，内存去重后返回分页前的完整 id 序列。

    去重依赖 normalize_news_title（跨库难以用 SQL 表达），故只取两列尽量降低开销。
    """
    stmt = (
        select(News.id, News.title)
        .where(News.category_id == category_id)
        .order_by(News.publish_time.desc(), News.id.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    seen_titles: set[str] = set()
    ids: list[int] = []
    for row in rows:
        dedupe_key = normalize_news_title(row.title) or str(row.id)
        if dedupe_key in seen_titles:
            continue
        seen_titles.add(dedupe_key)
        ids.append(row.id)
    return ids


async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    news_ids = await _load_latest_news_ids(db, category_id)
    page_ids = news_ids[skip: skip + limit]
    if not page_ids:
        return []

    stmt = select(News).where(News.id.in_(page_ids))
    result = await db.execute(stmt)
    rows_by_id = {item.id: item for item in result.scalars().all()}
    return [
        NewsItemBase.model_validate(rows_by_id[news_id]).model_dump(mode="json", by_alias=False)
        for news_id in page_ids
        if news_id in rows_by_id
    ]


async def get_news_count(db: AsyncSession, category_id: int):
    return len(await _load_latest_news_ids(db, category_id))


async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _escape_like(value: str) -> str:
    return value.replace("%", "").replace("_", "").strip()


async def get_hot_news(db: AsyncSession, category_id: int | None = None, skip: int = 0, limit: int = 10):
    """全库（或指定分类）按阅读量排序的热榜，聚合交给数据库完成。"""
    stmt = select(News).order_by(News.views.desc(), News.publish_time.desc(), News.id.desc())
    if category_id:
        stmt = stmt.where(News.category_id == category_id)
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_hot_news_count(db: AsyncSession, category_id: int | None = None):
    stmt = select(func.count()).select_from(News)
    if category_id:
        stmt = stmt.where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def search_news(db: AsyncSession, keyword: str, skip: int = 0, limit: int = 10):
    literal = _escape_like(keyword)
    if not literal:
        return []
    pattern = f"%{literal}%"
    stmt = (
        select(News)
        .where(or_(News.title.like(pattern), News.description.like(pattern)))
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def search_news_count(db: AsyncSession, keyword: str):
    literal = _escape_like(keyword)
    if not literal:
        return 0
    pattern = f"%{literal}%"
    stmt = (
        select(func.count())
        .select_from(News)
        .where(or_(News.title.like(pattern), News.description.like(pattern)))
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def search_news_by_keywords(db: AsyncSession, keywords: list[str], limit: int = 5):
    """按关键词粗筛候选新闻（LIKE 命中标题/简介），再在内存中按命中次数打分排序。

    关键词命中数过多会放大 SQL 条件，调用方应控制关键词数量（ai_context 里上限 16）。
    """
    conditions = []
    for keyword in keywords:
        # LIKE 通配符只按字面匹配，先剔除
        literal = keyword.replace("%", "").replace("_", "").strip()
        if len(literal) < 2:
            continue
        pattern = f"%{literal}%"
        conditions.append(News.title.like(pattern))
        conditions.append(News.description.like(pattern))

    if not conditions:
        return []

    stmt = (
        select(News)
        .where(or_(*conditions))
        .order_by(News.publish_time.desc(), News.id.desc())
        .limit(80)
    )
    result = await db.execute(stmt)
    candidates = result.scalars().all()

    scored = []
    for item in candidates:
        title_text = (item.title or "").casefold()
        description_text = (item.description or "").casefold()
        score = 0
        for keyword in keywords:
            literal = keyword.casefold()
            if literal in title_text:
                score += 3
            if literal in description_text:
                score += 1
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


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
        .limit(RELATED_SCAN_LIMIT)
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
