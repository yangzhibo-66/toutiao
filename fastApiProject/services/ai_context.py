"""AI 问答的"数据库优先"支持：从用户问题提取关键词，检索站内新闻作为回答上下文。

参照同类项目（fastapi-ai-news-platform）的做法：
- 命中站内新闻时，把资料注入 system 消息，让模型优先依据本地资料回答（省额度、答案更可信）
- 未配置 AI 服务时，直接用检索结果拼装兜底回答
中文没有空格分词，这里用 CJK 相邻二字串（bigram）近似关键词，英文取长度 >= 3 的词。
"""

import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from crud.news import search_news_by_keywords

# CJK 连续片段与英文/数字单词
_CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]+")
_ASCII_WORD_RE = re.compile(r"[a-zA-Z0-9]{3,}")
# 去除正文里的 HTML 标签（RSS 抓取的内容可能带标签）
_TAG_RE = re.compile(r"<[^>]+>")

MAX_KEYWORDS = 16
CONTEXT_NEWS_LIMIT = 5
CONTEXT_SNIPPET_LENGTH = 120

SYSTEM_PROMPT = (
    "你是新闻资讯助手。请优先依据下面的站内新闻资料回答用户问题，"
    "并注明参考了哪几条资料；资料与问题无关时可用通用知识简要回答。\n\n"
    "站内新闻资料：\n{context}"
)

DB_ONLY_ANSWER_HEADER = "根据站内新闻库，为你找到以下相关内容：\n\n"
DB_ONLY_MISS_ANSWER = (
    "当前未配置 AI 服务，且站内新闻库中没有找到与问题直接相关的内容。\n"
    "你可以换个问法，或到首页浏览最新新闻。"
)


def extract_keywords(question: str) -> list[str]:
    keywords: list[str] = []

    for run in _CJK_RUN_RE.findall(question or ""):
        if len(run) < 2:
            continue
        if len(run) == 2:
            keywords.append(run)
            continue
        # 长句无法穷举所有 bigram，均匀采样，保证覆盖整句
        step = max(1, (len(run) - 1) // MAX_KEYWORDS)
        keywords.extend(run[i: i + 2] for i in range(0, len(run) - 1, step))

    keywords.extend(word.casefold() for word in _ASCII_WORD_RE.findall(question or ""))
    return keywords[:MAX_KEYWORDS]


def _plain_text(value: str | None, max_length: int) -> str:
    text = _TAG_RE.sub("", value or "").strip()
    return text[:max_length]


def last_user_question(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content")
            return content if isinstance(content, str) else ""
    return ""


def _format_news_line(index: int, news_item) -> str:
    title = _plain_text(news_item.title, 80)
    snippet = _plain_text(news_item.description, CONTEXT_SNIPPET_LENGTH) or _plain_text(
        news_item.content, CONTEXT_SNIPPET_LENGTH
    )
    source = (news_item.author or "").strip() or "站内新闻"
    return f"{index}. **《{title}》**（{source}）：{snippet}"


async def build_ai_context(db: AsyncSession, messages: list[dict[str, Any]]) -> str:
    """检索与最后一条用户消息相关的站内新闻；无命中时返回空串（不注入上下文）。"""
    question = last_user_question(messages)
    keywords = extract_keywords(question)
    if not keywords:
        return ""

    news_items = await search_news_by_keywords(db, keywords, limit=CONTEXT_NEWS_LIMIT)
    if not news_items:
        return ""

    lines = [_format_news_line(i + 1, item) for i, item in enumerate(news_items)]
    return "\n".join(lines)


async def build_db_only_answer(db: AsyncSession, messages: list[dict[str, Any]]) -> str:
    """未配置 AI 服务时的兜底回答：直接整理站内检索结果。"""
    question = last_user_question(messages)
    keywords = extract_keywords(question)
    news_items = await search_news_by_keywords(db, keywords, limit=CONTEXT_NEWS_LIMIT) if keywords else []
    if not news_items:
        return DB_ONLY_MISS_ANSWER

    lines = [_format_news_line(i + 1, item) for i, item in enumerate(news_items)]
    return DB_ONLY_ANSWER_HEADER + "\n".join(lines)
