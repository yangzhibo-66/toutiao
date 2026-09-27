import logging
import os
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import ai_chat as crud_ai_chat
from models.users import User
from services.ai_context import (
    SYSTEM_PROMPT,
    build_ai_context,
    build_db_only_answer,
    last_user_question,
)
from utils.auth import get_current_user, get_optional_user
from utils.rate_limit import SlidingWindowLimiter, client_ip

router = APIRouter(prefix="/api/ai", tags=["ai"])

logger = logging.getLogger(__name__)

DASHSCOPE_API_ENDPOINT = os.getenv(
    "DASHSCOPE_API_ENDPOINT",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
).strip()
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "").strip()
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-max").strip()
AI_TIMEOUT_SECONDS = float(os.getenv("AI_CHAT_TIMEOUT_SECONDS", "90"))

# 每个 IP 每小时允许的对话次数，防止匿名请求消耗 AI 额度
_rate_limiter = SlidingWindowLimiter(
    max_events=int(os.getenv("AI_CHAT_RATE_LIMIT_PER_HOUR", "20")),
    window_seconds=3600,
)

AI_MAX_MESSAGES = int(os.getenv("AI_CHAT_MAX_MESSAGES", "20"))
AI_MAX_TOTAL_CHARS = int(os.getenv("AI_CHAT_MAX_TOTAL_CHARS", "16000"))


def _check_rate_limit(request: Request) -> None:
    _rate_limiter.check(client_ip(request), detail="AI 问答请求过于频繁，请稍后再试")


def _validate_messages(messages: list) -> list[dict]:
    total_chars = 0
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise HTTPException(status_code=400, detail="messages 格式不正确")
        total_chars += len(message["content"])
    if total_chars > AI_MAX_TOTAL_CHARS:
        raise HTTPException(status_code=400, detail="对话内容过长，请精简后再试")
    return messages


def _build_payload(payload: dict, messages: list[dict]) -> dict:
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")
    if len(messages) > AI_MAX_MESSAGES:
        raise HTTPException(status_code=400, detail="对话轮数过多，请开启新对话")

    return {
        # 模型只在服务端指定，不接受客户端传入，避免被指定昂贵模型消耗额度
        "model": DASHSCOPE_MODEL,
        "messages": _validate_messages(messages),
        "stream": bool(payload.get("stream", True)),
    }


def _sse_stream_text(text: str, on_complete=None) -> StreamingResponse:
    """以与上游一致的 OpenAI chunk 格式输出一段完整回答（供未配置 AI Key 时的兜底）。"""

    async def generate():
        chunk = {"choices": [{"delta": {"content": text}}]}
        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8")
        if on_complete is not None:
            try:
                await on_complete()
            except Exception as exc:
                logger.warning("保存 AI 问答记录失败: %s", exc)
        yield b"data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _collect_delta_content(line_bytes: bytes, collector: list[str]) -> None:
    """从上游 SSE 行中提取 delta.content，用于登录用户的历史记录保存。"""
    line = line_bytes.decode("utf-8", errors="ignore").strip()
    if not line.startswith("data:"):
        return
    data = line[5:].strip()
    if not data or data == "[DONE]":
        return
    try:
        parsed = json.loads(data)
    except ValueError:
        return
    choices = parsed.get("choices") or []
    delta = (choices[0].get("delta") or {}) if choices else {}
    content = delta.get("content")
    if isinstance(content, str):
        collector.append(content)


@router.post("/chat")
async def chat(
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    raw_body = await request.json()
    messages = raw_body.get("messages") if isinstance(raw_body, dict) else None
    if not isinstance(messages, list):
        messages = []

    _check_rate_limit(request)

    payload = _build_payload(raw_body if isinstance(raw_body, dict) else {}, messages)
    question = last_user_question(messages)

    async def save_history(answer_text: str) -> None:
        # 匿名请求不保存；回答为空也跳过
        if user is None or not answer_text.strip() or not question.strip():
            return
        await crud_ai_chat.save_chat(db, user.id, question, answer_text.strip())

    # 未配置 AI 服务时退化为"纯数据库回答"，接口格式保持 SSE 不变，前端零改动
    if not DASHSCOPE_API_KEY:
        answer = await build_db_only_answer(db, messages)
        return _sse_stream_text(answer, on_complete=lambda: save_history(answer))

    # 数据库优先：检索站内新闻作为上下文注入，未命中时保持原有透传行为
    context = await build_ai_context(db, messages)
    if context:
        payload["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
            *payload["messages"],
        ]

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
        "X-DashScope-SSE": "enable",
    }

    async def stream_response():
        collected: list[str] = []
        byte_buffer = b""
        failed = False
        timeout = httpx.Timeout(AI_TIMEOUT_SECONDS, connect=20)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    DASHSCOPE_API_ENDPOINT,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code >= 400:
                        failed = True
                        error_text = await response.aread()
                        detail = error_text.decode("utf-8", errors="ignore") or "AI request failed"
                        error_payload = {
                            "error": {
                                "message": f"AI request failed: HTTP {response.status_code} {detail}"
                            }
                        }
                        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n".encode("utf-8")
                        yield b"data: [DONE]\n\n"
                        return
                    async for chunk in response.aiter_bytes():
                        yield chunk
                        # 顺带收集回答内容用于保存历史（\n 不会出现在多字节 UTF-8 序列内部，按字节切行安全）
                        byte_buffer += chunk
                        while b"\n" in byte_buffer:
                            line_bytes, byte_buffer = byte_buffer.split(b"\n", 1)
                            _collect_delta_content(line_bytes, collected)
        except Exception as exc:
            failed = True
            error_payload = {"error": {"message": f"AI proxy failed: {exc}"}}
            yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"
            return

        if not failed:
            try:
                await save_history("".join(collected))
            except Exception as exc:
                logger.warning("保存 AI 问答记录失败: %s", exc)

    return StreamingResponse(stream_response(), media_type="text/event-stream")


@router.get("/history")
async def get_ai_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    items, total = await crud_ai_chat.get_user_history(db, user.id, offset, page_size)
    return {
        "code": 200,
        "message": "获取问答记录成功",
        "data": {
            "list": [
                {
                    "id": item.id,
                    "message": item.message,
                    "response": item.response,
                    "createdAt": item.created_at,
                }
                for item in items
            ],
            "total": total,
            "hasMore": offset + len(items) < total,
        },
    }


@router.delete("/history/{chat_id}")
async def delete_ai_history(
    chat_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await crud_ai_chat.delete_user_chat(db, user.id, chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="问答记录不存在")
    return {
        "code": 200,
        "message": "删除问答记录成功",
        "data": {"id": chat_id},
    }
