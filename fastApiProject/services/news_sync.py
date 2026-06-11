import asyncio
import html
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote_plus

import feedparser
import httpx
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import AsyncSessionLocal, async_engine
from crud.news import normalize_news_title
from models.news import Category, News

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"
WORLD_NEWS_API_BASE = "https://api.worldnewsapi.com/search-news"
DEFAULT_LOCALE = os.getenv("NEWS_SYNC_LOCALE", "zh-CN")
DEFAULT_REGION = os.getenv("NEWS_SYNC_REGION", "CN")
DEFAULT_EDITION = os.getenv("NEWS_SYNC_EDITION", "CN:zh-Hans")
SYNC_INTERVAL_MINUTES = int(os.getenv("NEWS_SYNC_INTERVAL_MINUTES", "1440"))
RUN_ON_STARTUP = os.getenv("NEWS_SYNC_RUN_ON_STARTUP", "true").lower() in {"1", "true", "yes", "on"}
MAX_ITEMS_PER_FEED = int(os.getenv("NEWS_SYNC_MAX_ITEMS", "15"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("NEWS_SYNC_HTTP_TIMEOUT", "20"))
NEWS_PROVIDER = os.getenv("NEWS_PROVIDER", "").strip().lower()
WORLD_NEWS_API_KEY = os.getenv("WORLD_NEWS_API_KEY", "").strip()

TAG_RE = re.compile(r"<[^>]+>")
IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)

TOPIC_HEADLINE = "头条"
TOPIC_SOCIETY = "社会"
TOPIC_DOMESTIC = "国内"
TOPIC_WORLD = "国际"
TOPIC_ENTERTAINMENT = "娱乐"
TOPIC_SPORTS = "体育"
TOPIC_MILITARY = "军事"
TOPIC_TECH = "科技"
TOPIC_FINANCE = "财经"
DEFAULT_AUTHOR = "新闻聚合"


@dataclass(frozen=True)
class FeedDefinition:
    category_name: str
    query: str
    worldnews_text: str = ""
    worldnews_category: str | None = None
    worldnews_source_country: str | None = None


FEEDS: list[FeedDefinition] = [
    FeedDefinition(TOPIC_HEADLINE, "热点新闻 when:2d", worldnews_category="politics"),
    FeedDefinition(TOPIC_SOCIETY, "社会新闻 when:2d", worldnews_text="社会新闻"),
    FeedDefinition(TOPIC_DOMESTIC, "中国新闻 when:2d", worldnews_text="中国新闻", worldnews_source_country="cn"),
    FeedDefinition(TOPIC_WORLD, "国际新闻 when:2d", worldnews_text="国际新闻"),
    FeedDefinition(TOPIC_ENTERTAINMENT, "娱乐新闻 when:2d", worldnews_category="entertainment"),
    FeedDefinition(TOPIC_SPORTS, "体育新闻 when:2d", worldnews_category="sports"),
    FeedDefinition(TOPIC_MILITARY, "军事新闻 when:2d", worldnews_text="军事新闻"),
    FeedDefinition(TOPIC_TECH, "科技新闻 when:2d", worldnews_category="technology"),
    FeedDefinition(TOPIC_FINANCE, "财经新闻 when:2d", worldnews_category="business"),
]

SYNC_STATUS: dict[str, Any] = {
    "running": False,
    "last_started_at": None,
    "last_finished_at": None,
    "last_result": None,
    "last_error": None,
}


def get_sync_status() -> dict[str, Any]:
    return dict(SYNC_STATUS)


def _use_world_news_api() -> bool:
    if NEWS_PROVIDER == "worldnewsapi":
        return bool(WORLD_NEWS_API_KEY)
    if NEWS_PROVIDER == "rss":
        return False
    return bool(WORLD_NEWS_API_KEY)


def _current_provider_name(used_worldnews: bool, used_rss: bool) -> str:
    if used_worldnews and used_rss:
        return "worldnewsapi+rss"
    if used_worldnews:
        return "worldnewsapi"
    return "google-rss"


async def ensure_sync_schema() -> None:
    async with async_engine.begin() as conn:
        def has_source_url(sync_conn):
            inspector = inspect(sync_conn)
            columns = inspector.get_columns("news")
            return any(column["name"] == "source_url" for column in columns)

        source_exists = await conn.run_sync(has_source_url)
        if not source_exists:
            await conn.execute(text("ALTER TABLE news ADD COLUMN source_url VARCHAR(500)"))


def _build_feed_url(query: str) -> str:
    encoded_query = quote_plus(query)
    return (
        f"{GOOGLE_NEWS_RSS_BASE}?q={encoded_query}"
        f"&hl={DEFAULT_LOCALE}&gl={DEFAULT_REGION}&ceid={DEFAULT_EDITION}"
    )


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    text_value = TAG_RE.sub(" ", value)
    text_value = html.unescape(text_value)
    text_value = re.sub(r"\s+", " ", text_value)
    return text_value.strip()


def _normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", "", _strip_html(value))


def _extract_image(entry: Any) -> str | None:
    media_content = entry.get("media_content") or []
    for item in media_content:
        url = item.get("url")
        if url:
            return url

    media_thumbnail = entry.get("media_thumbnail") or []
    for item in media_thumbnail:
        url = item.get("url")
        if url:
            return url

    summary = entry.get("summary", "") or ""
    match = IMG_RE.search(summary)
    if match:
        return html.unescape(match.group(1))
    return None


def _extract_source_url(entry: Any) -> str | None:
    for key in ("link", "id"):
        value = entry.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    links = entry.get("links") or []
    for item in links:
        href = item.get("href")
        if href and str(href).startswith("http"):
            return str(href)
    return None


def _parse_publish_time(entry: Any) -> datetime:
    raw_value = entry.get("published") or entry.get("updated") or ""
    if raw_value:
        try:
            parsed = parsedate_to_datetime(raw_value)
            if parsed.tzinfo is not None:
                return parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except (TypeError, ValueError):
            pass
    return datetime.utcnow()


def _build_content(entry: Any) -> tuple[str, str]:
    title = (entry.get("title") or "").strip()
    summary = _strip_html(entry.get("summary") or "")
    description = summary[:500] if summary else title[:500]

    if summary:
        normalized_title = re.sub(r"\s+", "", title)
        normalized_summary = re.sub(r"\s+", "", summary)
        if normalized_summary == normalized_title or normalized_title in normalized_summary:
            content = summary
        else:
            content = f"{title}\n\n{summary}"
    else:
        content = title

    return description, content


async def _fetch_feed(client: httpx.AsyncClient, feed: FeedDefinition) -> list[dict[str, Any]]:
    url = _build_feed_url(feed.query)
    response = await client.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ToutiaoNewsBot/1.0; +https://news.google.com)"
        },
    )
    response.raise_for_status()

    parsed_feed = feedparser.parse(response.content)
    items: list[dict[str, Any]] = []
    for entry in parsed_feed.entries[:MAX_ITEMS_PER_FEED]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue

        description, content = _build_content(entry)
        items.append(
            {
                "category_name": feed.category_name,
                "title": title,
                "description": description,
                "content": content,
                "image": _extract_image(entry),
                "source_url": _extract_source_url(entry),
                "author": entry.get("source", {}).get("title") or entry.get("author") or DEFAULT_AUTHOR,
                "publish_time": _parse_publish_time(entry),
            }
        )
    return items


async def _fetch_worldnews_feed(client: httpx.AsyncClient, feed: FeedDefinition) -> list[dict[str, Any]]:
    latest_publish_date = datetime.utcnow()
    earliest_publish_date = latest_publish_date - timedelta(days=2)
    base_params = {
        "api-key": WORLD_NEWS_API_KEY,
        "language": "zh",
        "earliest-publish-date": earliest_publish_date.strftime("%Y-%m-%d %H:%M:%S"),
        "latest-publish-date": latest_publish_date.strftime("%Y-%m-%d %H:%M:%S"),
        "sort": "publish-time",
        "sort-direction": "desc",
        "number": MAX_ITEMS_PER_FEED,
    }
    params = dict(base_params)
    if feed.worldnews_text:
        params["text"] = feed.worldnews_text
    if feed.worldnews_category:
        params["categories"] = feed.worldnews_category
    if feed.worldnews_source_country:
        params["source-country"] = feed.worldnews_source_country

    headers = {"User-Agent": "Mozilla/5.0 (compatible; ToutiaoNewsBot/1.0)"}
    response = await client.get(WORLD_NEWS_API_BASE, params=params, headers=headers)
    if response.status_code == 400 and "text" in params:
        fallback_params = dict(base_params)
        if feed.worldnews_category:
            fallback_params["categories"] = feed.worldnews_category
        if feed.worldnews_source_country:
            fallback_params["source-country"] = feed.worldnews_source_country
        response = await client.get(WORLD_NEWS_API_BASE, params=fallback_params, headers=headers)
    response.raise_for_status()
    payload = response.json()

    items: list[dict[str, Any]] = []
    for article in payload.get("news", [])[:MAX_ITEMS_PER_FEED]:
        title = (article.get("title") or "").strip()
        text_value = (article.get("text") or "").strip()
        if not title or not text_value:
            continue

        publish_time = article.get("publish_date") or ""
        parsed_time = datetime.utcnow()
        if publish_time:
            try:
                parsed_time = datetime.fromisoformat(publish_time.replace("Z", "+00:00"))
                if parsed_time.tzinfo is not None:
                    parsed_time = parsed_time.astimezone(timezone.utc).replace(tzinfo=None)
            except ValueError:
                parsed_time = datetime.utcnow()

        authors = article.get("authors") or []
        author = authors[0] if authors else None
        items.append(
            {
                "category_name": feed.category_name,
                "title": title,
                "description": (article.get("summary") or text_value[:200]).strip()[:500],
                "content": text_value,
                "image": article.get("image"),
                "source_url": article.get("url"),
                "author": author or DEFAULT_AUTHOR,
                "publish_time": parsed_time,
            }
        )
    return items


async def _load_category_map(db: AsyncSession) -> dict[str, int]:
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return {item.name: item.id for item in categories}


async def _load_existing_news_map(db: AsyncSession, category_id: int, titles: list[str]) -> dict[str, News]:
    if not titles:
        return {}
    result = await db.execute(
        select(News).where(News.category_id == category_id)
    )
    existing_map: dict[str, News] = {}
    for item in result.scalars().all():
        existing_map[item.title] = item
        normalized_title = normalize_news_title(item.title)
        if normalized_title and normalized_title not in existing_map:
            existing_map[normalized_title] = item
    return existing_map


def _content_score(value: str | None) -> int:
    text_value = _strip_html(value)
    if not text_value:
        return 0

    score = len(text_value)
    if "\n\n" in text_value:
        score += 120
    score += min(len(re.findall(r"[。！？.!?]", text_value)), 12) * 30
    return score


def _should_replace_content(existing: News, incoming_content: str) -> bool:
    incoming_score = _content_score(incoming_content)
    if incoming_score <= 0:
        return False

    existing_score = _content_score(existing.content)
    if incoming_score >= existing_score + 120:
        return True

    existing_normalized = _normalize_text(existing.content)
    incoming_normalized = _normalize_text(incoming_content)
    if not existing_normalized:
        return True
    if incoming_normalized and existing_normalized in incoming_normalized and len(incoming_normalized) > len(existing_normalized):
        return True
    return False


async def sync_news(db: AsyncSession) -> dict[str, Any]:
    category_map = await _load_category_map(db)
    fetched_items: list[dict[str, Any]] = []
    used_worldnews = False
    used_rss = False
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
        for feed in FEEDS:
            if feed.category_name not in category_map:
                logger.warning("Skip feed for missing category: %s", feed.category_name)
                continue
            try:
                if _use_world_news_api():
                    try:
                        worldnews_items = await _fetch_worldnews_feed(client, feed)
                        if worldnews_items:
                            used_worldnews = True
                        fetched_items.extend(worldnews_items)
                    except httpx.HTTPStatusError as exc:
                        if exc.response is not None and exc.response.status_code == 402:
                            logger.warning(
                                "World News API quota/payment unavailable for %s, fallback to RSS",
                                feed.category_name,
                            )
                            rss_items = await _fetch_feed(client, feed)
                            if rss_items:
                                used_rss = True
                            fetched_items.extend(rss_items)
                        else:
                            raise
                else:
                    rss_items = await _fetch_feed(client, feed)
                    if rss_items:
                        used_rss = True
                    fetched_items.extend(rss_items)
            except Exception as exc:
                logger.exception("Failed to fetch feed for %s: %s", feed.category_name, exc)

    grouped_items: dict[int, list[dict[str, Any]]] = {}
    for item in fetched_items:
        category_id = category_map.get(item["category_name"])
        if not category_id:
            continue
        grouped_items.setdefault(category_id, []).append(item)

    inserted = 0
    updated = 0
    skipped = 0
    for category_id, items in grouped_items.items():
        titles = [item["title"] for item in items]
        existing_news_map = await _load_existing_news_map(db, category_id, titles)
        for item in items:
            normalized_title = normalize_news_title(item["title"])
            existing_news = existing_news_map.get(item["title"]) or existing_news_map.get(normalized_title)
            if existing_news:
                changed = False

                if _should_replace_content(existing_news, item["content"]):
                    existing_news.content = item["content"]
                    changed = True

                incoming_description = (item["description"] or "").strip()
                if incoming_description and (
                    not existing_news.description or len(incoming_description) > len(existing_news.description or "")
                ):
                    existing_news.description = incoming_description
                    changed = True

                if item["image"] and not existing_news.image:
                    existing_news.image = item["image"]
                    changed = True

                if item["source_url"] and (
                    not existing_news.source_url or "news.google.com" in (existing_news.source_url or "")
                ):
                    existing_news.source_url = item["source_url"]
                    changed = True

                if item["author"] and (not existing_news.author or existing_news.author == DEFAULT_AUTHOR):
                    existing_news.author = item["author"]
                    changed = True

                if item["publish_time"] and (
                    not existing_news.publish_time or item["publish_time"] > existing_news.publish_time
                ):
                    existing_news.publish_time = item["publish_time"]
                    changed = True

                if changed:
                    db.add(existing_news)
                    existing_news_map[item["title"]] = existing_news
                    if normalized_title:
                        existing_news_map[normalized_title] = existing_news
                    updated += 1
                else:
                    skipped += 1
                continue

            new_news = News(
                title=item["title"],
                description=item["description"],
                content=item["content"],
                image=item["image"],
                source_url=item["source_url"],
                author=item["author"],
                category_id=category_id,
                views=0,
                publish_time=item["publish_time"],
            )
            db.add(new_news)
            existing_news_map[item["title"]] = new_news
            if normalized_title:
                existing_news_map[normalized_title] = new_news
            inserted += 1

    await db.commit()
    return {
        "provider": _current_provider_name(used_worldnews, used_rss),
        "fetched": len(fetched_items),
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "categories": len(grouped_items),
    }


async def run_sync_once() -> dict[str, Any]:
    await ensure_sync_schema()
    SYNC_STATUS["running"] = True
    SYNC_STATUS["last_started_at"] = datetime.utcnow().isoformat()
    SYNC_STATUS["last_error"] = None
    try:
        async with AsyncSessionLocal() as session:
            result = await sync_news(session)
        SYNC_STATUS["last_result"] = result
        return result
    except Exception as exc:
        SYNC_STATUS["last_error"] = str(exc)
        logger.exception("News sync failed: %s", exc)
        raise
    finally:
        SYNC_STATUS["running"] = False
        SYNC_STATUS["last_finished_at"] = datetime.utcnow().isoformat()


async def sync_loop(stop_event: asyncio.Event) -> None:
    if RUN_ON_STARTUP:
        try:
            await run_sync_once()
        except Exception:
            logger.exception("Initial news sync failed")

    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=SYNC_INTERVAL_MINUTES * 60)
        except asyncio.TimeoutError:
            try:
                await run_sync_once()
            except Exception:
                logger.exception("Scheduled news sync failed")
