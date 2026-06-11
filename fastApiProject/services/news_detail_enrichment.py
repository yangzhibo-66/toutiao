import html
import json
import logging
import re
from html.parser import HTMLParser

import httpx
import trafilatura
from sqlalchemy.ext.asyncio import AsyncSession

from models.news import News
from utils.google_news import decode_google_news_url, is_google_news_url

try:
    from readability import Document
except ImportError:  # pragma: no cover - optional dependency
    Document = None

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 20
MIN_CONTENT_LENGTH = 150
MAX_PARAGRAPHS = 14
WHITESPACE_RE = re.compile(r"\s+")
JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])")
BOILERPLATE_RE = re.compile(
    r"(责任编辑|责编|来源[:：]|原标题|点击|扫码|APP|免责声明|版权归|返回搜狐|相关新闻|延伸阅读|更多精彩|本文转自)",
    re.IGNORECASE,
)


def _clean_text(value: str) -> str:
    text = html.unescape(value or "")
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", _clean_text(value))


def _is_sparse_content(news: News) -> bool:
    content = _clean_text(news.content or "")
    if len(content) < MIN_CONTENT_LENGTH:
        return True
    title = _clean_text(news.title or "")
    if title and content.startswith(title) and len(content.replace(title, "", 1).strip()) < 80:
        return True
    return False


def _looks_like_boilerplate(text: str) -> bool:
    cleaned = _clean_text(text)
    if not cleaned:
        return True
    if len(cleaned) <= 3:
        return True
    return bool(BOILERPLATE_RE.search(cleaned))


def _split_long_paragraph(text: str, chunk_size: int = 120) -> list[str]:
    cleaned = _clean_text(text)
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    sentences = [part.strip() for part in SENTENCE_SPLIT_RE.split(cleaned) if part.strip()]
    if len(sentences) <= 1:
        return [cleaned]

    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        if not buffer:
            buffer = sentence
            continue
        if len(buffer) + len(sentence) > chunk_size:
            chunks.append(buffer.strip())
            buffer = sentence
        else:
            buffer += sentence
    if buffer:
        chunks.append(buffer.strip())
    return chunks


def _prepare_paragraphs(parts: list[str], title: str | None = None) -> list[str]:
    normalized_title = _normalize_text(title or "")
    prepared: list[str] = []
    seen: set[str] = set()

    for part in parts:
        for chunk in _split_long_paragraph(part):
            cleaned = _clean_text(chunk)
            normalized = _normalize_text(cleaned)
            if not cleaned or not normalized:
                continue
            if normalized_title and normalized == normalized_title:
                continue
            if _looks_like_boilerplate(cleaned):
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            prepared.append(cleaned)
            if len(prepared) >= MAX_PARAGRAPHS:
                return prepared
    return prepared


def _join_paragraphs(parts: list[str], title: str | None = None) -> str | None:
    paragraphs = _prepare_paragraphs(parts, title=title)
    if not paragraphs:
        return None
    content = "\n\n".join(paragraphs).strip()
    if len(_clean_text(content)) < MIN_CONTENT_LENGTH:
        return None
    return content


def _iter_json_like_nodes(payload):
    if isinstance(payload, dict):
        yield payload
        for value in payload.values():
            yield from _iter_json_like_nodes(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_json_like_nodes(item)


def _extract_json_ld_text(html_text: str, title: str | None = None) -> str | None:
    text_candidates: list[str] = []

    for raw_json in JSON_LD_RE.findall(html_text):
        raw_json = raw_json.strip()
        if not raw_json:
            continue
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            continue

        for node in _iter_json_like_nodes(payload):
            if not isinstance(node, dict):
                continue
            for key in ("articleBody", "text", "description"):
                value = node.get(key)
                if isinstance(value, str) and len(_clean_text(value)) >= 80:
                    text_candidates.append(value)

    return _join_paragraphs(text_candidates, title=title)


class ArticleHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.capture_tag = None
        self.current_parts: list[str] = []
        self.paragraphs: list[str] = []
        self.block_parts: list[str] = []
        self.blocks: list[str] = []
        self.og_image = None
        self.meta_description = None

    def handle_starttag(self, tag, attrs):
        attrs_map = dict(attrs)
        if tag in {"script", "style"}:
            if tag == "script":
                self.in_script = True
            else:
                self.in_style = True
            return

        if tag == "meta":
            prop = attrs_map.get("property") or attrs_map.get("name")
            if prop in {"og:image", "twitter:image"} and not self.og_image:
                self.og_image = attrs_map.get("content")
            if prop in {"description", "og:description"} and not self.meta_description:
                self.meta_description = attrs_map.get("content")
            return

        if tag in {"p", "h2", "h3", "li"}:
            self.capture_tag = tag
            self.current_parts = []

        if tag in {"article", "main", "section", "div"}:
            if self.block_parts:
                text = _clean_text(" ".join(self.block_parts))
                if len(text) >= 80 and text not in self.blocks:
                    self.blocks.append(text)
            self.block_parts = []

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
            return
        if tag == "style":
            self.in_style = False
            return

        if self.capture_tag == tag:
            text = _clean_text(" ".join(self.current_parts))
            if len(text) >= 20 and text not in self.paragraphs:
                self.paragraphs.append(text)
            self.capture_tag = None
            self.current_parts = []

        if tag in {"article", "main", "section", "div"}:
            text = _clean_text(" ".join(self.block_parts))
            if len(text) >= 80 and text not in self.blocks:
                self.blocks.append(text)
            self.block_parts = []

    def handle_data(self, data):
        if self.in_script or self.in_style:
            return
        cleaned = _clean_text(data)
        if not cleaned:
            return
        if self.capture_tag:
            self.current_parts.append(cleaned)
        self.block_parts.append(cleaned)


async def _fetch_article(url: str) -> tuple[str, str | None]:
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.google.com/",
        },
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text, str(response.url)


def _extract_with_trafilatura(html_text: str, title: str | None = None) -> str | None:
    extracted = trafilatura.extract(
        html_text,
        output_format="txt",
        include_comments=False,
        include_tables=False,
        include_images=False,
        favor_recall=True,
        deduplicate=True,
    )
    if not extracted:
        return None
    parts = [part.strip() for part in re.split(r"\n{2,}", extracted) if part.strip()]
    return _join_paragraphs(parts, title=title)


def _extract_with_readability(html_text: str, title: str | None = None) -> str | None:
    if Document is None:
        return None
    try:
        doc = Document(html_text)
        summary_html = doc.summary()
    except Exception:
        return None
    return _extract_with_trafilatura(summary_html, title=title)


def _extract_with_html_parser(html_text: str, title: str | None = None) -> tuple[str | None, str | None]:
    parser = ArticleHTMLParser()
    parser.feed(html_text)

    content = _join_paragraphs(parser.paragraphs, title=title)
    if content:
        return content, parser.og_image

    ranked_blocks = sorted(parser.blocks, key=len, reverse=True)
    content = _join_paragraphs(ranked_blocks[:6], title=title)
    if content:
        return content, parser.og_image

    meta_description = _join_paragraphs([parser.meta_description or ""], title=title)
    return meta_description, parser.og_image


def _extract_article_content(html_text: str, title: str | None = None) -> tuple[str | None, str | None]:
    json_ld_content = _extract_json_ld_text(html_text, title=title)
    if json_ld_content:
        parser = ArticleHTMLParser()
        parser.feed(html_text)
        return json_ld_content, parser.og_image

    trafilatura_content = _extract_with_trafilatura(html_text, title=title)
    if trafilatura_content:
        parser = ArticleHTMLParser()
        parser.feed(html_text)
        return trafilatura_content, parser.og_image

    readability_content = _extract_with_readability(html_text, title=title)
    if readability_content:
        parser = ArticleHTMLParser()
        parser.feed(html_text)
        return readability_content, parser.og_image

    return _extract_with_html_parser(html_text, title=title)


async def maybe_enrich_news_detail(db: AsyncSession, news: News) -> News:
    if not news.source_url:
        return news

    if is_google_news_url(news.source_url):
        decoded_url = decode_google_news_url(news.source_url)
        if decoded_url and decoded_url != news.source_url:
            news.source_url = decoded_url
            db.add(news)
            await db.commit()
            await db.refresh(news)

    if not _is_sparse_content(news) and news.image:
        return news

    try:
        html_text, final_url = await _fetch_article(news.source_url)
        content, image = _extract_article_content(html_text, title=news.title)
    except Exception as exc:
        logger.warning("Failed to enrich news detail %s: %s", news.id, exc)
        return news

    changed = False
    if final_url and final_url != news.source_url:
        news.source_url = final_url
        changed = True

    if content and len(_clean_text(content)) > len(_clean_text(news.content or "")):
        news.content = content
        if not news.description or len(news.description.strip()) < 40:
            news.description = content.split("\n\n", 1)[0][:500]
        changed = True

    if image and not news.image:
        news.image = image
        changed = True

    if changed:
        db.add(news)
        await db.commit()
        await db.refresh(news)

    return news
